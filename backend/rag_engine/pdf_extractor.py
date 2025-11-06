"""
Módulo de extracción de texto desde PDFs
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2


class PDFExtractor:
    """Extrae texto de archivos PDF y lo cachea"""
    
    def __init__(self, pdf_dir: str, cache_dir: str):
        self.pdf_dir = Path(pdf_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extrae texto de un PDF página por página
        
        Returns:
            Dict con número de página como clave y texto como valor
        """
        pages_text = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text[page_num] = text.strip()
                        
        except Exception as e:
            print(f"Error extrayendo {pdf_path.name}: {e}")
            
        return pages_text
    
    def get_cache_path(self, pdf_path: Path) -> Path:
        """Retorna la ruta del archivo de caché para un PDF"""
        cache_name = pdf_path.stem + ".txt"
        return self.cache_dir / cache_name
    
    def is_cached(self, pdf_path: Path) -> bool:
        """Verifica si el PDF ya tiene caché válido"""
        cache_path = self.get_cache_path(pdf_path)
        
        if not cache_path.exists():
            return False
        
        # Verificar que el caché sea más reciente que el PDF
        pdf_mtime = pdf_path.stat().st_mtime
        cache_mtime = cache_path.stat().st_mtime
        
        return cache_mtime >= pdf_mtime
    
    def save_to_cache(self, pdf_path: Path, pages_text: Dict[int, str]) -> None:
        """Guarda el texto extraído en caché"""
        cache_path = self.get_cache_path(pdf_path)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            for page_num, text in sorted(pages_text.items()):
                f.write(f"=== PÁGINA {page_num} ===\n")
                f.write(text)
                f.write("\n\n")
    
    def load_from_cache(self, pdf_path: Path) -> Dict[int, str]:
        """Carga texto desde caché"""
        cache_path = self.get_cache_path(pdf_path)
        pages_text = {}
        
        if not cache_path.exists():
            return pages_text
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear el formato de caché
        sections = content.split("=== PÁGINA ")
        for section in sections[1:]:
            lines = section.split("\n", 1)
            page_num = int(lines[0].split(" ===")[0])
            text = lines[1].strip() if len(lines) > 1 else ""
            if text:
                pages_text[page_num] = text
        
        return pages_text
    
    def process_pdf(self, pdf_path: Path, force: bool = False) -> Dict[int, str]:
        """
        Procesa un PDF: usa caché si existe, o extrae y cachea
        
        Args:
            pdf_path: Ruta al PDF
            force: Si True, fuerza la re-extracción aunque exista caché
        """
        if not force and self.is_cached(pdf_path):
            return self.load_from_cache(pdf_path)
        
        pages_text = self.extract_text_from_pdf(pdf_path)
        
        if pages_text:
            self.save_to_cache(pdf_path, pages_text)
        
        return pages_text
    
    def process_all_pdfs(self, force: bool = False) -> Dict[str, Dict[int, str]]:
        """
        Procesa todos los PDFs en el directorio
        
        Returns:
            Dict con nombre de archivo como clave y páginas como valor
        """
        all_documents = {}
        
        if not self.pdf_dir.exists():
            return all_documents
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        for pdf_path in pdf_files:
            print(f"Procesando {pdf_path.name}...")
            pages_text = self.process_pdf(pdf_path, force=force)
            
            if pages_text:
                all_documents[pdf_path.name] = pages_text
        
        return all_documents
