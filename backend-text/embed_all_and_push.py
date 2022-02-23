# This script creates embeddings for every Document and pushes the DocumentArray to the cloud
# so other people can skip the slow embedding process and just pull embeddings directly via DocumentArray.pull()

from jina import Flow
from helper import csv_to_docarray, remove_tensor
from config import DEVICE, CSV_FILE, TIMEOUT_READY

MAX_DOCS = 9999999

pushed_name = "fashion-product-images-clip-all"

def embed_docs():

    flow = (
        Flow()
        .add(
            uses=f"jinahub://CLIPImageEncoder/v0.4",
            name="image_encoder",
            uses_with={"device": DEVICE},
            install_requirements=True,
            uses_metas={"timeout_ready": TIMEOUT_READY},
            replicas=2,
        )
    )

    with flow:
        docs = flow.index(inputs=docs, show_progress=True, return_results=True)

    return docs

print("Creating intial docarray")
docs = csv_to_docarray(file_path=CSV_FILE, max_docs=MAX_DOCS)

# Create embeddings
print("Embedding docs via Flow")
embedded_docs = embed_docs()

# Remove tensors to save space
print("Removing tensors to save space")
embedded_docs.apply(remove_tensor)

# Push to cloud so others can download later
print(f"Pushing to cloud with name {pushed_name}")
embedded_docs.push(pushed_name)