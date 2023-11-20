from configparser import ConfigParser
import heapq
from typing import Dict, List, Union
import numpy as np

from torch import Tensor
import torch
from data.datastructures.evidence import Evidence
from data.datastructures.question import Question
from metrics.SimilarityMatch import SimilarityMetric
from retriever.BaseRetriever import BaseRetriver
from sentence_transformers import SentenceTransformer
import logging


class ANCE(BaseRetriver):

    def __init__(self,config_path="config.ini",show_progress_bar=True,convert_to_tensor=True,batch_size=None) -> None:
        super().__init__()
        self.config = ConfigParser()
        self.config.read(config_path)
        self.question_encoder = SentenceTransformer(self.config["Retrieval"]["question-encoder"])
        self.context_encoder = SentenceTransformer(self.config["Retrieval"]["context-encoder"])
        self.show_progress_bar = show_progress_bar
        self.convert_to_tensor = convert_to_tensor
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
    
    def encode_queries(self, queries: List[Question], batch_size: int = 16, **kwargs) -> Union[List[Tensor], np.ndarray, Tensor]:
        queries = [query.text() for query in queries]
        return self.question_encoder.encode(queries, batch_size=batch_size)
    
    def encode_corpus(self, corpus: List[Evidence],sep:str=None, batch_size: int = 8, **kwargs) -> Union[List[Tensor], np.ndarray, Tensor]:
        contexts = []
        for evidence in corpus:
            context = ""
            if evidence.title():
                context = (evidence.title() + self.sep + evidence.text()).strip()
            else:
                context = evidence.text().strip()
            contexts.append(context)
        return self.context_encoder.encode(contexts, batch_size=batch_size)


    def retrieve(self, 
               corpus: List[Evidence], 
               queries: List[Question], 
               top_k: int, 
               score_function: SimilarityMetric,
               return_sorted: bool = False, 
               batch_size: int=16,
               sep: str="#",
               **kwargs) -> Dict[str, Dict[str, float]]:

        
        self.logger.info("Encoding Queries...")
        query_ids = [query.id() for query in queries]
        self.results = {qid: {} for qid in query_ids}
        self.batch_size = batch_size
        self.sep = sep
        query_embeddings = self.encode_queries(queries, batch_size=self.batch_size)
          
        self.logger.info("Sorting Corpus by document length (Longest first)...")

        corpus = sorted(corpus, key=lambda evidence: len(evidence.title() + self.sep + evidence.text() if evidence.title() else evidence.text()), reverse=True)
   
        self.logger.info("Encoding Corpus in batches... Warning: This might take a while!")
        self.logger.info("Scoring Function: {} ({})".format(score_function.name(), score_function))
        
        corpus_embeddings = self.encode_corpus(corpus)

        # Compute similarites using either cosine-similarity or dot product
        cos_scores = score_function.evaluate(query_embeddings,corpus_embeddings)
        # Get top-k values
        cos_scores_top_k_values, cos_scores_top_k_idx = torch.topk(cos_scores, min(top_k+1, len(cos_scores[0])), dim=1, largest=True, sorted=return_sorted)
        cos_scores_top_k_values = cos_scores_top_k_values.cpu().tolist()
        cos_scores_top_k_idx = cos_scores_top_k_idx.cpu().tolist()

        qrels = {}
        for q in range(len(cos_scores_top_k_idx)):
            qid = queries[q].id()
            qrels[qid] = {}
            for doc in cos_scores_top_k_idx[q]:
                qrels[qid][corpus[doc].id()] = cos_scores[q][doc].item()
                
        return qrels 
