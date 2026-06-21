from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .rag.pipeline import answer_question
from .models import QuestionHistory, ChatSession


@staff_member_required
def admin_ask_page(request, chat_id=None):
    chats = ChatSession.objects.filter(
        user=request.user
    ).order_by("-created_at")

    if chat_id:
        current_chat = get_object_or_404(
            ChatSession,
            id=chat_id,
            user=request.user
        )
    else:
        current_chat = chats.first()

        if current_chat is None:
            current_chat = ChatSession.objects.create(
                title="New Chat",
                user=request.user
            )

    if request.method == "POST":
        question = request.POST.get("question")

        if question:
            result = answer_question(
                question,
                user=request.user,
                debug=True
            )

            answer = result["answer"]
            sources = result.get("sources", [])

            if (
                not current_chat.title
                or current_chat.title.startswith("New Chat")
            ):
                current_chat.title = question[:60]
                current_chat.save()

            QuestionHistory.objects.create(
                chat=current_chat,
                question=question,
                answer=answer,
                sources=sources
            )

        return redirect(
            "admin_ask_chat",
            chat_id=current_chat.id
        )

    messages = QuestionHistory.objects.filter(
        chat=current_chat
    ).order_by("created_at")

    return render(
        request,
        "admin/ask_documents.html",
        {
            "chats": chats,
            "current_chat": current_chat,
            "messages": messages,
        }
    )


@staff_member_required
def delete_admin_chat(request, chat_id):
    chat = get_object_or_404(
        ChatSession,
        id=chat_id,
        user=request.user
    )

    chat.delete()

    remaining = ChatSession.objects.filter(
        user=request.user
    ).order_by("-created_at")

    if remaining.exists():
        return redirect(
            "admin_ask_chat",
            chat_id=remaining.first().id
        )

    return redirect("new_admin_chat")
def new_admin_chat(request):
    chat = ChatSession.objects.create(
        title="New Chat",
        user=request.user
    )

    return redirect(
        "admin_ask_chat",
        chat_id=chat.id
    )


@api_view(["POST"])
def ask(request):
    question = request.data.get("question")
    debug = request.data.get("debug", False)

    user = request.user if request.user.is_authenticated else None

    chat = ChatSession.objects.create(
        title=question[:60] if question else "API Chat",
        user=user
    )

    result = answer_question(
        question,
        user=user,
        debug=True
    )

    answer = result["answer"]
    retrieved_chunks = result.get("retrieved_chunks", [])
    sources = result.get("sources", [])

    QuestionHistory.objects.create(
        chat=chat,
        question=question,
        answer=answer,
        sources=sources
    )

    response_data = {
        "question": question,
        "answer": answer,
        "chat_id": chat.id,
    }

    if debug:
        response_data["retrieved_chunks"] = retrieved_chunks
        response_data["sources"] = sources

    return Response(response_data)