from docarray import Document
from jina import Flow
from helper import input_docs_from_csv, get_columns
from config import DEVICE, MAX_DOCS, WORKSPACE_DIR, PORT, CSV_FILE, DIMS, TIMEOUT_READY
import click
import pickle

def index(csv_file=CSV_FILE, max_docs=MAX_DOCS):
    docs = input_docs_from_csv(file_path=csv_file, max_docs=max_docs)

    columns = get_columns(docs[0]) # Get all the column info from first doc
    pickle.dump(columns, open("columns.p", "wb")) # Pickle values so search fn can pick up later

    flow_index = (
        Flow()
        # .add(
            # uses="jinahub://DocCache/v0.1", 
            # name="deduplicator",
            # install_requirements=True,
        # )
        .add(
            uses="jinahub://CLIPImageEncoder/v0.4",
            name="image_encoder",
            uses_with={"device": DEVICE},
            install_requirements=True,
            uses_metas={"timeout_ready": TIMEOUT_READY},
        )
        .add(
            uses="jinahub://PQLiteIndexer/v0.2.3-rc",
            name="indexer",
            uses_with={
                'dim': DIMS,
                'columns': columns,
                # 'columns': COLUMNS,
                'metric': "cosine",
                'include_metadata': True
            },
            uses_metas={"workspace": WORKSPACE_DIR},
            volumes=f"./{WORKSPACE_DIR}:/workspace/workspace",
            install_requirements=True
        )
    )

    with flow_index:
        flow_index.index(inputs=docs, show_progress=True)


def search():
    columns = pickle.load(open("columns.p", "rb"))
    flow_search = (
        Flow(protocol="http", port_expose=PORT)
        .add(
            uses="jinahub://CLIPTextEncoder/v0.2",
            name="text_encoder",
            uses_with={"device": DEVICE},
            install_requirements=True,
        )
        .add(
            uses="jinahub://PQLiteIndexer/v0.2.3-rc",
            name="indexer",
            uses_with={
                'dim': DIMS,
                'columns': columns,
                'metric': "cosine",
                'include_metadata': True
            },
            uses_metas={"workspace": WORKSPACE_DIR},
            volumes=f"./{WORKSPACE_DIR}:/workspace/workspace",
            install_requirements=True
        )
    )

    with flow_search:
        # flow_search.port_expose = PORT
        # flow_search.cors = True
        # flow_search.protocol = "http"
        flow_search.block()

def search_grpc():
    columns = pickle.load(open("columns.p", "rb"))
    flow_search = (
        Flow()
        .add(
            uses="jinahub://CLIPTextEncoder/v0.2",
            name="text_encoder",
            uses_with={"device": DEVICE},
            install_requirements=True,
        )
        .add(
            uses="jinahub://PQLiteIndexer/v0.2.3-rc",
            name="indexer",
            uses_with={
                'dim': DIMS,
                'columns': columns,
                'metric': "cosine",
                'include_metadata': True
            },
            uses_metas={"workspace": WORKSPACE_DIR},
            volumes=f"./{WORKSPACE_DIR}:/workspace/workspace",
            install_requirements=True
        )
    )

    with flow_search:
        results = flow_search.search(Document(text="shoes"), return_results=True)
        print([result.text for result in results])


@click.command()
@click.option(
    "--task",
    "-t",
    type=click.Choice(["index", "search", "search_grpc"], case_sensitive=False),
)
@click.option("--num_docs", "-n", default=MAX_DOCS)
def main(task: str, num_docs: int):
    if task == "index":
        index(csv_file=CSV_FILE, max_docs=num_docs)
    elif task == "search":
        search()
    elif task == "search_grpc":
        search_grpc()


if __name__ == "__main__":
    main()
