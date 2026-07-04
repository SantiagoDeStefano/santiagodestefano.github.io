import os, time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, udf, input_file_name, get_json_object
from pyspark.sql.types import ArrayType, StringType

BASE = "/mnt/e/redpajama-data"
OUT = "/mnt/e/redpajama-chunks"
CHUNK_SIZE = 2048

spark = SparkSession.builder \
    .appName("RedPajama Batch Chunker") \
    .master("local[12]") \
    .config("spark.driver.memory", "40g") \
    .config("spark.local.dir", "mnt/f/spark-temp") \
    .config("spark.ui.showConsoleProgress", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

def chunk_text(text):
    if not text:
        return []
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE):
        piece = text[i : i + CHUNK_SIZE].strip()
        if piece:
            chunks.append(piece)
    return chunks

chunk_udf = udf(chunk_text, ArrayType(StringType()))

folders = {}
for root, _, fnames in os.walk(BASE):
    for f in fnames:
        if f.endswith(".jsonl") or f.endswith(".json"):
            subdir = os.path.relpath(root, BASE).split(os.sep)[0]
            folders.setdefault(subdir, []).append(os.path.join(root, f))

