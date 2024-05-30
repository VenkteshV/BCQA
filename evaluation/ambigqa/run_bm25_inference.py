from data.loaders.RetrieverDataset import RetrieverDataset
from config.constants import Split
from retriever.lexical.bm25 import BM25Search
from utils.metrics.retrieval.RetrievalMetrics import RetrievalMetrics


if __name__ == "__main__":

    # config = config_instance.get_all_params()

    loader = RetrieverDataset("ambignq","ambignq-corpus",
                               "evaluation/config.ini", Split.DEV,tokenizer=None)
    queries, qrels, corpus = loader.qrels()
    print("queries",len(queries),len(qrels),len(corpus),queries[0])
    bm25_search = BM25Search(index_name="ambigqa",initialize=False)

    ## wikimultihop
    

    # with open("/raid_data-lv/venktesh/BCQA/wiki_musique_corpus.json") as f:
    #     corpus = json.load(f)

    response = bm25_search.retrieve(corpus,queries,100)
    print("indices",len(response))
    metrics = RetrievalMetrics(k_values=[1,10,100])
    print(metrics.evaluate_retrieval(qrels=qrels,results=response))