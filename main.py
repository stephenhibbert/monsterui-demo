from fasthtml.common import *
from claudette import *
from anthropic import AnthropicBedrock
from monsterui.core import *

# Set up the app with FrankenUI theme and markdown support
hdrs = [
    Theme.blue.headers(),
    MarkdownJS(),
    HighlightJS(langs=['python', 'javascript', 'html', 'css']),
]
app, rt = fast_app(hdrs=hdrs)

# Set up chat model
ab = AnthropicBedrock(aws_region='us-east-1')
cli = Client("anthropic.claude-3-haiku-20240307-v1:0", ab)
sp = "You are a helpful and concise assistant."


def ChatMessage(msg, user, loading=False, id=None):
    cls = 'flex items-center gap-2 ' + ('justify-end' if user else 'justify-start')
    msg_cls = ('bg-primary text-primary-foreground' if user else 'bg-muted') + ' p-3 rounded-lg max-w-[80%]'

    if loading:
        return Div(id=id, cls=cls)(
            Div("Thinking...", cls=msg_cls + " animate-pulse")
        )

    # If it's a user message, just show plain text
    if user:
        return Div(cls=cls)(
            Div(msg, cls=msg_cls)
        )

    # For Claude's responses, use markdown rendering
    return Div(cls=cls)(
        Div(msg, cls=f"{msg_cls} mt-4 my-4 marked")
    )


def ChatInput():
    return Input(
        name='msg',
        id='msg-input',
        placeholder="Type a message...",
        cls="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
        required=True,
        hx_swap_oob='true'
    )


@rt('/')
def index():
    return Titled("Chat with Claude",
                  Container(
                      # Messages div outside the form so copy button doesn't try to submit the form
                      Div(id="chat-messages", cls="space-y-4 h-[80vh] overflow-y-auto p-4"),
                      # Form only wraps the input area
                      Form(
                          Div(cls="flex gap-2 mt-4")(
                              ChatInput(),
                              Button("Send", cls=ButtonT.primary, hx_disable="true")
                          ),
                          hx_post='/chat',
                          hx_swap="beforeend",
                          hx_target="#chat-messages",
                          hx_validate="true",
                          hx_indicator="#msg-input"
                      )
                  ))


@rt('/chat')
def chat(msg: str):
    if not msg or not msg.strip():
        return ""

    loading_id = "loading-message"
    return (
        ChatMessage(msg.strip(), True),
        ChatMessage("", False, loading=True, id=loading_id),
        ChatInput(),
        Form(
            Hidden(id="msg", value=msg),
            hx_post='/chat/response',
            hx_trigger="load",
            hx_target=f"#{loading_id}",
            hx_swap="outerHTML"
        )
    )


@rt('/chat/response')
def post(msg: str, messages: list[str] = None):
    if not messages: messages = []
    messages.append(msg)
    response = contents(cli(messages, sp=sp))
    return ChatMessage(response.rstrip(), False)


serve()