from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Document, ChatSession, QuestionHistory
from .rag.pipeline import answer_question


def render_sources(obj):
    if not obj.sources:
        return "-"

    html = "<strong>Sources:</strong><br>"

    for source in obj.sources:
        title = source.get("title", "Unknown")
        chunk_id = source.get("chunk_id", "?")
        source_type = source.get("source_type", "")

        if source_type:
            html += f"• {title} (chunk {chunk_id}, {source_type})<br>"
        else:
            html += f"• {title} (chunk {chunk_id})<br>"

    return mark_safe(html)


class QuestionInline(admin.TabularInline):
    model = QuestionHistory
    extra = 1

    fields = (
        "question",
        "answer",
        "formatted_sources",
        "created_at",
    )

    readonly_fields = (
        "answer",
        "formatted_sources",
        "created_at",
    )

    def formatted_sources(self, obj):
        return render_sources(obj)

    formatted_sources.short_description = "Sources"


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "created_at",
    )

    search_fields = (
        "title",
        "user__username",
    )

    ordering = ("-created_at",)
    inlines = [QuestionInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user

        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.user == request.user

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in instances:
            if isinstance(obj, QuestionHistory):
                old_question = None

                if obj.pk:
                    try:
                        old_obj = QuestionHistory.objects.get(pk=obj.pk)
                        old_question = old_obj.question
                    except QuestionHistory.DoesNotExist:
                        old_question = None

                should_generate_answer = False

                if obj.question:
                    if not obj.pk:
                        should_generate_answer = True
                    elif old_question != obj.question:
                        should_generate_answer = True
                    elif not obj.answer:
                        should_generate_answer = True

                if should_generate_answer:
                    result = answer_question(
                        obj.question,
                        user=request.user,
                        debug=True
                    )

                    obj.answer = result.get("answer", "")
                    obj.sources = result.get("sources", [])

                obj.chat = form.instance
                obj.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


@admin.register(QuestionHistory)
class QuestionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat",
        "short_question",
        "short_answer",
        "created_at",
    )

    search_fields = (
        "question",
        "answer",
        "chat__title",
    )

    readonly_fields = (
        "answer",
        "formatted_sources",
        "created_at",
    )

    fields = (
        "chat",
        "question",
        "answer",
        "formatted_sources",
        "created_at",
    )

    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(chat__user=request.user)

    def formatted_sources(self, obj):
        return render_sources(obj)

    formatted_sources.short_description = "Sources"

    def save_model(self, request, obj, form, change):
        should_generate_answer = False

        if obj.question:
            if not obj.pk:
                should_generate_answer = True
            elif "question" in form.changed_data:
                should_generate_answer = True
            elif not obj.answer:
                should_generate_answer = True

        if should_generate_answer:
            result = answer_question(
                obj.question,
                user=request.user,
                debug=True
            )

            obj.answer = result.get("answer", "")
            obj.sources = result.get("sources", [])

        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.chat and obj.chat.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.chat and obj.chat.user == request.user

    def short_question(self, obj):
        return obj.question[:80]

    short_question.short_description = "Question"

    def short_answer(self, obj):
        return obj.answer[:100]

    short_answer.short_description = "Answer"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "is_private",
        "created_at",
    )

    list_filter = (
        "is_private",
        "created_at",
    )

    search_fields = (
        "title",
        "content",
        "user__username",
    )

    readonly_fields = (
        "content",
        "created_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(user=request.user)

    def get_fields(self, request, obj=None):
        fields = [
            "title",
            "file",
            "is_private",
            "content",
            "created_at",
        ]

        if request.user.is_superuser:
            fields.insert(2, "user")

        return fields

    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            if not obj.user:
                obj.user = request.user
        else:
            obj.user = request.user

        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return request.user.is_staff

        return obj.user == request.user
    
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "username",
                "password",
            )
        }),
        ("Personal info", {
            "fields": (
                "first_name",
                "last_name",
                "email",
            )
        }),
        ("Access", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    list_display = (
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
    )