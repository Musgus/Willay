"""
Motor RAG principal que coordina extracción, chunking, embeddings y búsqueda
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from .pdf_extractor import PDFExtractor
from .chunker import TextChunker, EmbeddingGenerator
from .vector_store import VectorStore


class RAGEngine:
    """Motor principal para gestionar el pipeline RAG completo"""
    
    def __init__(
        self,
        pdf_dir: str = "rag",
        cache_dir: str = "backend/rag_engine/cache",
        vector_store_dir: str = "backend/rag_engine/vector_store",
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 800,
        chunk_overlap: int = 200
    ):
        """
        Inicializa el motor RAG con todos sus componentes
        
        Args:
            pdf_dir: Directorio con los PDFs
            cache_dir: Directorio para cachear texto extraído
            vector_store_dir: Directorio para persistir embeddings
            embedding_model: Modelo de Ollama para embeddings
            chunk_size: Tamaño de los chunks en caracteres
            chunk_overlap: Overlap entre chunks
        """
        self.pdf_extractor = PDFExtractor(pdf_dir, cache_dir)
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.vector_store = VectorStore(vector_store_dir)
        self.pdf_dir = Path(pdf_dir)
        
        # Crear directorio de PDFs si no existe
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
    
    async def index_documents(self, force: bool = False) -> Dict:
        """
        Indexa todos los PDFs: extrae texto, chunking, embeddings y almacena
        
        Args:
            force: Si True, fuerza la re-indexación aunque ya exista caché
        
        Returns:
            Dict con estadísticas del proceso
        """
        print("🔄 Iniciando indexación de documentos...")
        
        # 1. Extraer texto de PDFs
        all_documents = self.pdf_extractor.process_all_pdfs(force=force)
        
        if not all_documents:
            print("⚠️  No se encontraron PDFs en el directorio")
            return {"status": "no_documents", "total_chunks": 0}
        
        print(f"✓ Extraídos {len(all_documents)} documentos")
        
        # 2. Crear chunks con metadata
        all_chunks = []
        for filename, pages_text in all_documents.items():
            chunks = self.chunker.chunk_document(pages_text, filename)
            all_chunks.extend(chunks)
        
        print(f"✓ Creados {len(all_chunks)} chunks")
        
        # 3. Generar embeddings
        texts = [chunk["text"] for chunk in all_chunks]
        metadatas = [chunk["metadata"] for chunk in all_chunks]
        
        print("🔄 Generando embeddings (esto puede tomar varios minutos)...")
        embeddings = await self.embedding_generator.generate_embeddings_batch(texts)
        
        print(f"✓ Generados {len(embeddings)} embeddings")
        
        # 4. Guardar en vector store
        ids = [f"chunk_{meta['chunk_id']}" for meta in metadatas]
        self.vector_store.add_documents(texts, embeddings, metadatas, ids)
        
        stats = self.vector_store.get_stats()
        
        print("✅ Indexación completada")
        return {
            "status": "success",
            "total_chunks": stats["total_chunks"],
            "total_files": stats["total_files"],
            "files": stats["files"]
        }
    
    async def search_context(
        self,
        query: str,
        n_results: int = 5,
        filename_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca contexto relevante para una consulta
        
        Args:
            query: Texto de la consulta del usuario
            n_results: Cantidad de chunks a recuperar
            filename_filter: Filtrar por nombre de archivo específico
        
        Returns:
            Lista de chunks relevantes con metadata
        """
        # Generar embedding de la consulta
        query_embedding = await self.embedding_generator.generate_embedding(query)
        
        # Buscar en vector store
        filter_meta = {"filename": filename_filter} if filename_filter else None
        results = self.vector_store.search(
            query_embedding,
            n_results=n_results,
            filter_metadata=filter_meta
        )
        
        # Formatear resultados
        context_chunks = []
        for i, (doc, meta, distance) in enumerate(
            zip(results["documents"], results["metadatas"], results["distances"])
        ):
            context_chunks.append({
                "text": doc,
                "filename": meta["filename"],
                "page": meta["page"],
                "relevance_score": 1 - distance,  # Convertir distancia a score
                "rank": i + 1
            })
        
        return context_chunks
    
    def build_rag_prompt(
        self,
        query: str,
        context_chunks: List[Dict],
        system_prompt: str
    ) -> str:
        """
        Construye un prompt enriquecido con contexto RAG
        
        Args:
            query: Pregunta del usuario
            context_chunks: Chunks recuperados del vector store
            system_prompt: Prompt del sistema base
        
        Returns:
            Prompt completo con contexto inyectado
        """
        if not context_chunks:
            return system_prompt
        
        # Construir sección de contexto
        context_section = "CONTEXTO DE DOCUMENTOS:\n\n"
        
        for chunk in context_chunks:
            context_section += f"[{chunk['filename']} - Página {chunk['page']}]\n"
            context_section += f"{chunk['text']}\n\n"
        
        context_section += "---\n\n"
        
        # Prompt mejorado que instruye al modelo a usar el contexto
        enhanced_prompt = f"""{system_prompt}

IMPORTANTE: Tienes acceso a los siguientes fragmentos de documentos que son relevantes para responder la pregunta del usuario. Usa esta información para dar respuestas precisas y cita las fuentes cuando sea apropiado.

{context_section}

Cuando respondas:
1. Usa la información de los documentos si es relevante
2. Menciona la fuente (archivo y página) cuando cites información
3. Si la información no está en los documentos, indícalo claramente
4. Mantén tus respuestas educativas y claras
"""
        
        return enhanced_prompt
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del sistema RAG"""
        return self.vector_store.get_stats()
    
    def clear_index(self) -> None:
        """Limpia completamente el índice"""
        self.vector_store.clear()
    
    def remove_document(self, filename: str) -> None:
        """Elimina un documento específico del índice"""
        self.vector_store.delete_by_filename(filename)
    
    def get_indexed_files(self) -> List[str]:
        """Retorna lista de archivos indexados"""
        return self.vector_store.get_filenames()
    
    def is_indexed(self) -> bool:
        """Verifica si hay documentos indexados"""
        return self.vector_store.count_documents() > 0
