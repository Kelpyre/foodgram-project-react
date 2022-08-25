from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('name', 'author', 'tags',)
    empty_value_display = '-пусто-'
    readonly_fields = ('count_favorites',)

    def count_favorites(self, obj):
        return obj.favorite.count()
    count_favorites.short_description = 'Добавлено в избранное, раз'


@admin.register(Ingredient)
class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


admin.site.register(Tag)
admin.site.register(RecipeIngredient)
admin.site.register(ShoppingList)
admin.site.register(Favorite)
