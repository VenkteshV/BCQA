import unittest

from config.constants import Split
from data.loaders.RetrieverDataset import RetrieverDataset
from utils.metrics.SimilarityMatch import CosineSimilarity
from utils.metrics.retrieval.RetrievalMetrics import RetrievalMetrics
from retriever.dense.ANCE import ANCE





class MyTestCase(unittest.TestCase):
    def test_retriever_dataloader(self):
        loader = RetrieverDataset("finqa","finqa-corpus","tests/retriever/test_config.ini",Split.DEV,tokenizer=None)
        retriever = ANCE("tests/retriever/test_config.ini")
        queries, qrels, corpus = loader.qrels()
        qrels_ret = retriever.retrieve(corpus,queries,100,CosineSimilarity(),True)
        self.assertEqual(len(qrels),len(qrels_ret))
        evaluator = RetrievalMetrics()
        ndcg, _map, recall, precision = evaluator.evaluate_retrieval(qrels,qrels_ret)



if __name__ == '__main__':
    unittest.main()