"""
Script CLI para gestionar la indexación de documentos RAG

Uso:
    python rag_cli.py index          # Indexar todos los PDFs
    python rag_cli.py index --force  # Forzar re-indexación
    python rag_cli.py stats          # Ver estadísticas
    python rag_cli.py clear          # Limpiar índice
    python rag_cli.py list           # Listar documentos indexados
"""
import asyncio
import sys
from pathlib import Path
from rag_engine import RAGEngine


def print_header(text: str):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"✅ {text}")


def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"❌ {text}")


def print_info(text: str):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {text}")


async def index_documents(rag: RAGEngine, force: bool = False):
    """Indexa todos los documentos"""
    print_header("INDEXACIÓN DE DOCUMENTOS")
    
    # Verificar que existan PDFs
    pdf_dir = Path("rag")
    pdfs = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    
    if not pdfs:
        print_error("No se encontraron archivos PDF en el directorio 'rag/'")
        print_info("Coloca tus archivos PDF en la carpeta 'rag/' y vuelve a intentar")
        return
    
    print_info(f"Encontrados {len(pdfs)} archivos PDF:")
    for pdf in pdfs:
        print(f"  • {pdf.name}")
    
    print()
    
    # Indexar
    stats = await rag.index_documents(force=force)
    
    if stats["status"] == "success":
        print_success("Indexación completada")
        print(f"\n📊 Estadísticas:")
        print(f"  • Total de chunks: {stats['total_chunks']}")
        print(f"  • Total de archivos: {stats['total_files']}")
        
        if stats["files"]:
            print(f"\n📚 Archivos indexados:")
            for file_info in stats["files"]:
                print(f"  • {file_info['filename']}")
                print(f"    - Chunks: {file_info['chunks']}")
                print(f"    - Páginas: {file_info['pages']}")
    else:
        print_error("No se pudieron indexar documentos")


async def show_stats(rag: RAGEngine):
    """Muestra estadísticas del índice"""
    print_header("ESTADÍSTICAS RAG")
    
    if not rag.is_indexed():
        print_info("No hay documentos indexados")
        print_info("Ejecuta 'python rag_cli.py index' para indexar")
        return
    
    stats = rag.get_stats()
    
    print(f"📊 Estado del índice:")
    print(f"  • Total de chunks: {stats['total_chunks']}")
    print(f"  • Total de archivos: {stats['total_files']}")
    
    if stats["files"]:
        print(f"\n📚 Archivos indexados:")
        for file_info in stats["files"]:
            print(f"\n  {file_info['filename']}")
            print(f"    • Chunks: {file_info['chunks']}")
            print(f"    • Páginas: {file_info['pages']}")


async def clear_index(rag: RAGEngine):
    """Limpia el índice completo"""
    print_header("LIMPIAR ÍNDICE")
    
    if not rag.is_indexed():
        print_info("El índice ya está vacío")
        return
    
    stats = rag.get_stats()
    print(f"⚠️  Se eliminarán {stats['total_chunks']} chunks de {stats['total_files']} archivos")
    
    confirm = input("\n¿Confirmas? (s/n): ").lower()
    
    if confirm == 's':
        rag.clear_index()
        print_success("Índice limpiado correctamente")
        print_info("Los archivos PDF originales se mantienen intactos")
    else:
        print_info("Operación cancelada")


async def list_files(rag: RAGEngine):
    """Lista archivos indexados"""
    print_header("DOCUMENTOS INDEXADOS")
    
    if not rag.is_indexed():
        print_info("No hay documentos indexados")
        return
    
    files = rag.get_indexed_files()
    
    print(f"📁 Total de archivos: {len(files)}\n")
    for i, filename in enumerate(files, 1):
        print(f"  {i}. {filename}")


async def watch_mode(rag: RAGEngine):
    """Modo observador: detecta cambios y re-indexa automáticamente"""
    print_header("MODO OBSERVADOR")
    print_info("Observando cambios en el directorio 'rag/'...")
    print_info("Presiona Ctrl+C para detener\n")
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class PDFHandler(FileSystemEventHandler):
            def __init__(self, rag_engine):
                self.rag = rag_engine
                self.indexing = False
            
            def on_created(self, event):
                if event.src_path.endswith('.pdf') and not self.indexing:
                    print(f"\n📄 Nuevo PDF detectado: {Path(event.src_path).name}")
                    self.reindex()
            
            def on_modified(self, event):
                if event.src_path.endswith('.pdf') and not self.indexing:
                    print(f"\n📝 PDF modificado: {Path(event.src_path).name}")
                    self.reindex()
            
            def on_deleted(self, event):
                if event.src_path.endswith('.pdf'):
                    print(f"\n🗑️  PDF eliminado: {Path(event.src_path).name}")
            
            def reindex(self):
                self.indexing = True
                print("🔄 Re-indexando...")
                asyncio.run(rag.index_documents())
                self.indexing = False
                print("✅ Re-indexación completada\n")
        
        event_handler = PDFHandler(rag)
        observer = Observer()
        observer.schedule(event_handler, "rag", recursive=False)
        observer.start()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n\n👋 Deteniendo observador...")
        
        observer.join()
        
    except ImportError:
        print_error("El módulo 'watchdog' no está instalado")
        print_info("Instala con: pip install watchdog")


async def main():
    """Función principal del CLI"""
    rag = RAGEngine()
    
    if len(sys.argv) < 2:
        print("Uso: python rag_cli.py <comando> [opciones]")
        print("\nComandos disponibles:")
        print("  index         Indexar todos los PDFs")
        print("  index --force Forzar re-indexación completa")
        print("  stats         Mostrar estadísticas")
        print("  clear         Limpiar índice")
        print("  list          Listar documentos indexados")
        print("  watch         Modo observador (auto-reindex)")
        return
    
    command = sys.argv[1].lower()
    
    if command == "index":
        force = "--force" in sys.argv
        await index_documents(rag, force=force)
    
    elif command == "stats":
        await show_stats(rag)
    
    elif command == "clear":
        await clear_index(rag)
    
    elif command == "list":
        await list_files(rag)
    
    elif command == "watch":
        await watch_mode(rag)
    
    else:
        print_error(f"Comando desconocido: {command}")
        print_info("Comandos válidos: index, stats, clear, list, watch")


if __name__ == "__main__":
    asyncio.run(main())
