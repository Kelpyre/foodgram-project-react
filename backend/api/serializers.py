from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from foodgram.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingList, Tag
)
from users.models import User, Subscription


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User

    def get_is_subscribed(self, obj):
        if self.context.get('request'):
            user = self.context.get('request').user
        else:
            user = obj
        if not user.is_authenticated:
            return False
        return Subscription.objects.filter(user=user, author=obj.id).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте, вспомогательный."""
    measurement_unit = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = RecipeIngredient

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""

    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        fields = (
            'name',
            'measurement_unit',
        )
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(
        read_only=True,
        default=CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipeingredient',
        required=True
    )
    image = Base64ImageField(use_url=True, required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def to_representation(self, instance):
        data = super(RecipeSerializer, self).to_representation(instance)
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        data['ingredients'] = RecipeIngredientSerializer(
            instance.recipeingredient.all(), many=True).data
        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы 1 игредиент'
            )

        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_id)
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингридиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)

            amount = ingredient_item.get('amount')
            if int(amount) <= 0:
                raise serializers.ValidationError('Проверьте, что количество'
                                                  'ингредиента больше нуля')

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один тэг!'
            })

        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Тэги должны быть уникальными!'
                })
            tags_list.append(tag)

        cooking_time = data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовление должно быть больше нуля!'
            })

        data['ingredients'] = ingredients
        data['tags'] = tags
        return data

    def ingredients_creation(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data.pop('recipeingredient')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.ingredients_creation(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        ingredients = validated_data.pop('ingredients')
        validated_data.pop('recipeingredient')
        self.ingredients_creation(ingredients, instance)
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)

    def validate(self, data):
        request = self.context.get('request')
        current_user = request.user
        recipe_in_favorite = Favorite.objects.filter(
            user=current_user,
            recipe=self.initial_data['recipe']
        )
        if request.method == 'POST':
            if recipe_in_favorite.exists():
                raise serializers.ValidationError({
                    'errors': 'Этот рецепт уже есть в избранном.'
                })
        if request.method == 'DELETE':
            if not recipe_in_favorite.exists():
                raise serializers.ValidationError({
                    'errors': 'Этого рецепта нет в избранном.'
                })
        return data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор модели корзины."""
    image = Base64ImageField(use_url=True, required=True)
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    cooking_time = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = ShoppingList

    def get_id(self, obj):
        return obj.id

    def get_name(self, obj):
        return obj.name

    def get_cooking_time(self, obj):
        return obj.cooking_time

    def validate(self, data):
        request = self.context.get('request')
        current_user = request.user
        recipe_in_shopping_list = ShoppingList.objects.filter(
            user=current_user,
            recipe=self.initial_data['recipe']
        )
        if request.method == 'POST':
            if recipe_in_shopping_list.exists():
                raise serializers.ValidationError({
                    'errors': 'Этот рецепт уже есть в списке покупок.'
                })
        if request.method == 'DELETE':
            if not recipe_in_shopping_list.exists():
                raise serializers.ValidationError({
                    'errors':
                    'Этого рецепта нет в списке покупок пользователя.'
                })
        return data


class UserSubscriptionSerializer(CustomUserSerializer):
    """Сериализатор подписки пользователя."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes
        if limit:
            recipes = recipes.all()[:int(limit)]
        context = {'request': request}
        return ShoppingListSerializer(recipes, context=context, many=True).data

    def validate(self, data):
        request = self.context.get('request')
        current_user = request.user
        author = self.initial_data['author']
        in_subscribed = Subscription.objects.filter(
            user=current_user,
            author=author
        )
        if request.method == 'POST':
            if in_subscribed.exists():
                raise serializers.ValidationError({
                    'errors': 'Вы уже подписаны на этого автора.'
                })
            if author == current_user:
                raise serializers.ValidationError({
                    'errors': 'Нельзя подписаться на себя.'
                })
        if request.method == 'DELETE':
            if not in_subscribed.exists():
                raise serializers.ValidationError({
                    'errors': 'Вы не подписаны на этого автора.'
                })
        return data
