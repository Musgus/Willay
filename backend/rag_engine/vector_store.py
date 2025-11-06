"""
Vector Store usando ChromaDB para almacenar y buscar embeddings
"""
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
from pathlib import Path


class VectorStore:
    """Almacena y busca embeddings usando ChromaDB"""
    
    def __init__(self, persist_dir: str = "backend/rag_engine/vector_store"):
        """
        Inicializa ChromaDB con persistencia local
        
        Args:
            persist_dir: Directorio donde se guardarán los datos
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar ChromaDB para persistencia
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Crear o obtener colección
        self.collection_name = "willay_documents"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Willay RAG knowledge base"}
        )
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[np.ndarray],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Agrega documentos al vector store
        
        Args:
            texts: Lista de textos (chunks)
            embeddings: Lista de embeddings correspondientes
            metadatas: Lista de metadatos para cada chunk
            ids: IDs únicos para cada documento (se genera si no se provee)
        """
        if not ids:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        # Convertir embeddings a listas (ChromaDB no acepta numpy directamente)
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        # Agregar en lotes para evitar problemas de memoria
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = embeddings_list[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            self.collection.add(
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        print(f"✓ Agregados {len(texts)} chunks al vector store")
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict[str, List]:
        """
        Busca documentos similares usando un embedding de consulta
        
        Args:
            query_embedding: Embedding de la consulta
            n_results: Número de resultados a retornar
            filter_metadata: Filtros opcionales (ej: {"filename": "libro.pdf"})
        
        Returns:
            Dict con keys: documents, metadatas, distances
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=filter_metadata
        )
        
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def get_all_documents(self) -> Dict[str, List]:
        """Retorna todos los documentos del vector store"""
        results = self.collection.get()
        return results
    
    def count_documents(self) -> int:
        """Retorna la cantidad de documentos en el store"""
        return self.collection.count()
    
    def clear(self) -> None:
        """Elimina todos los documentos del vector store"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Willay RAG knowledge base"}
        )
        print("✓ Vector store limpiado")
    
    def delete_by_filename(self, filename: str) -> None:
        """Elimina todos los chunks de un archivo específico"""
        # ChromaDB no soporta delete con where directamente,
        # necesitamos obtener los IDs primero
        results = self.collection.get(where={"filename": filename})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            print(f"✓ Eliminados {len(results['ids'])} chunks de {filename}")
    
    def get_filenames(self) -> List[str]:
        """Retorna lista de archivos únicos en el vector store"""
        results = self.collection.get()
        if not results["metadatas"]:
            return []
        
        filenames = set(meta["filename"] for meta in results["metadatas"])
        return sorted(list(filenames))
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del vector store"""
        all_docs = self.collection.get()
        
        if not all_docs["metadatas"]:
            return {
                "total_chunks": 0,
                "total_files": 0,
                "files": []
            }
        
        filenames = {}
        for meta in all_docs["metadatas"]:
            filename = meta["filename"]
            if filename not in filenames:
                filenames[filename] = {"chunks": 0, "pages": set()}
            filenames[filename]["chunks"] += 1
            filenames[filename]["pages"].add(meta["page"])
        
        files_info = [
            {
                "filename": fname,
                "chunks": info["chunks"],
                "pages": len(info["pages"])
            }
            for fname, info in filenames.items()
        ]
        
        return {
            "total_chunks": len(all_docs["metadatas"]),
            "total_files": len(filenames),
            "files": files_info
        }
