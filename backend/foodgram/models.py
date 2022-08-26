from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тэгов."""
    name = models.CharField('Название', max_length=50, unique=True)
    slug = models.SlugField('Уникальный слаг', unique=True)
    color = models.CharField(
        'Цвет в HEX',
        max_length=50,
        unique=True,
        default='#ffffff'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    name = models.CharField(
        verbose_name='Название',
        max_length=256,
        db_index=True,
        unique=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список id тегов',
        related_name='tags',
        blank=True,
        db_index=True
    )
    image = models.ImageField('Картинка', upload_to='recipe/',)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        through='RecipeIngredient',
        db_index=True
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для связи рецептов с ингредиентами, вспомогательная."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Название рецепта',
        on_delete=models.CASCADE,
        related_name='recipeingredient',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Название ингредиента',
        on_delete=models.CASCADE,
        related_name='recipeingredient',
    )
    amount = models.PositiveSmallIntegerField('Количество',)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient',
            ),
        ]
        ordering = ['recipe']
        verbose_name = 'Рецепт-Ингредиент'
        verbose_name_plural = 'Рецепты-Ингредиенты'


class ShoppingList(models.Model):
    """Модель корзины."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppinglist',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='shoppinglist',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppinglist',
            ),
        ]
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_follow'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
