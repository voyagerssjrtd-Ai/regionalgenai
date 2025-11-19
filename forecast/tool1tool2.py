import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langgraph_supervisor import create_supervisor
from langchain_core.messages import convert_to_messages

load_dotenv()

def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return
    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)

def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        if len(ns) == 0:
            return
        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label
        print(update_label + "\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]
        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")

async def run_agent(query):
    client = MultiServerMCPClient(
        {
            "dairysales": {
                "command": "python",
                "args": ["dairysales_server.py"],
                "transport": "stdio",
            },
            "pdfquery": {
                "command": "python",
                "args": ["pdfquery_server.py"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()
    model = init_chat_model(model="openai:gpt-4.1", api_key=os.getenv("OPENAI_API_KEY"))

    # Agent 1: transforms forecasting questions into historical queries
    query_transformer_agent = create_react_agent(
        model,
        tools=[],
        prompt="""You are a query transformation assistant.
        Your task is to convert forecasting questions into historical data retrieval queries.
        Example:
        User: Predict the sales for next 12 months for the ghee product
        You: Provide monthly sales data for Ghee from the past 3 years
        Always return a single, clear, structured query suitable for retrieving historical data.""",
        name="query_transformer_agent"
    )

    # Agent 2: retrieves dairy sales data
    dairy_agent = create_react_agent(
        model,
        tools,
        prompt="""You are a dairy sales analyst. Answer questions about historical dairy sales using structured CSV data.
        Use year/month filters when available. Be precise and avoid hallucinating values.""",
        name="dairy_agent"
    )

    # Agent 3: retrieves full PDF context
    pdf_agent = create_react_agent(
        model,
        tools,
        prompt="""You are a document analyst. Use the tool to retrieve all semantically chunked sections from a PDF.
        Return the full structured content. Do not summarize or interpret it.""",
        name="pdf_agent"
    )

    # Agent 4: generates prediction from sales + PDF context
    prediction_agent = create_react_agent(
        model,
        tools=[],
        prompt="""You are a forecasting assistant.

        You will receive:
        - Historical sales data for a dairy product
        - Domain knowledge from a PDF (e.g., seasonal trends, product usage)

        Your task is to:
        1. Analyze the sales trend
        2. Use the PDF context to understand influencing factors
        3. Predict sales for the next 12 months

        Return a structured forecast with month-by-month estimates and a brief rationale.""",
        name="prediction_agent"
    )

    # Supervisor orchestrates the flow
    supervisor = create_supervisor(
        model=model,
        agents=[query_transformer_agent, dairy_agent, pdf_agent, prediction_agent],
        prompt=(
            "You are a supervisor managing four agents:\n"
            "- query_transformer_agent: transforms forecasting questions into historical queries\n"
            "- dairy_agent: retrieves historical dairy sales data\n"
            "- pdf_agent: retrieves full chunked PDF content\n"
            "- prediction_agent: compares both and generates a forecast\n\n"
            "If the user asks for predictions:\n"
            "1. Call query_transformer_agent\n"
            "2. Pass its output to dairy_agent\n"
            "3. Call pdf_agent to get full document context\n"
            "4. Pass both outputs to prediction_agent\n"
            "Do not answer yourself. Do not ask the user to proceed."
        ),
        add_handoff_back_messages=True,
        output_mode="full_history"
    ).compile()

    for chunk in supervisor.stream({
        "messages": [
            {"role": "user", "content": query}
        ]
    }):
        pretty_print_messages(chunk, last_message=True)

if __name__ == "__main__":
    asyncio.run(run_agent("Predict the sales for next 12 months for the ghee product"))