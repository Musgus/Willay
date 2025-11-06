"""
Módulo para dividir texto en chunks y crear embeddings
"""
import re
from typing import List, Dict, Tuple
import numpy as np


class TextChunker:
    """Divide texto en fragmentos manejables"""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 200):
        """
        Args:
            chunk_size: Tamaño aproximado en caracteres de cada chunk
            overlap: Cantidad de caracteres que se solapan entre chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto"""
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        # Eliminar caracteres especiales problemáticos
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
        return text.strip()
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones"""
        # Patrón simple para detectar fin de oración
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_chunks(self, text: str) -> List[str]:
        """
        Crea chunks del texto respetando límites de oraciones
        
        Returns:
            Lista de chunks de texto
        """
        text = self.clean_text(text)
        sentences = self.split_by_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Si agregar esta oración excede el tamaño, guardar el chunk actual
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Iniciar nuevo chunk con overlap
                words = current_chunk.split()
                overlap_text = " ".join(words[-self.overlap // 5:])  # Aprox overlap en palabras
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Agregar el último chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_document(
        self, 
        pages_text: Dict[int, str], 
        filename: str
    ) -> List[Dict[str, any]]:
        """
        Convierte un documento completo en chunks con metadata
        
        Args:
            pages_text: Dict con número de página y texto
            filename: Nombre del archivo fuente
        
        Returns:
            Lista de dicts con: text, metadata (filename, page, chunk_id)
        """
        chunks_with_metadata = []
        global_chunk_id = 0
        
        for page_num, page_text in sorted(pages_text.items()):
            page_chunks = self.create_chunks(page_text)
            
            for local_id, chunk_text in enumerate(page_chunks):
                chunks_with_metadata.append({
                    "text": chunk_text,
                    "metadata": {
                        "filename": filename,
                        "page": page_num,
                        "chunk_id": global_chunk_id,
                        "local_chunk_id": local_id,
                        "char_count": len(chunk_text)
                    }
                })
                global_chunk_id += 1
        
        return chunks_with_metadata


class EmbeddingGenerator:
    """Genera embeddings usando Ollama localmente"""
    
    def __init__(self, model: str = "nomic-embed-text"):
        """
        Args:
            model: Modelo de embeddings de Ollama (nomic-embed-text, mxbai-embed-large)
        """
        self.model = model
        self.dimension = 768  # nomic-embed-text usa 768 dimensiones
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Genera embedding para un texto usando Ollama
        
        Returns:
            Array numpy con el embedding
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://127.0.0.1:11434/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                return np.array(data["embedding"], dtype=np.float32)
        except Exception as e:
            print(f"Error generando embedding: {e}")
            # Retornar embedding cero en caso de error
            return np.zeros(self.dimension, dtype=np.float32)
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 10
    ) -> List[np.ndarray]:
        """
        Genera embeddings para múltiples textos en lotes
        
        Args:
            texts: Lista de textos
            batch_size: Cantidad de textos por lote
        
        Returns:
            Lista de embeddings
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Generando embeddings {i+1}-{min(i+batch_size, len(texts))} de {len(texts)}...")
            
            for text in batch:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
        
        return embeddings
