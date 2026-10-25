import os
import shutil
import time
import re
import pymupdf
from pymupdf import pymupdf4llm

BASE_DIR = r"d:\Users\shuichi\Documents\AI\Flash"
EXTRACTED_DIR = os.path.join(BASE_DIR, "extracted")
IMAGES_DIR = os.path.join(EXTRACTED_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

targets = [
    {
        "pdf": "W25.pdf",
        "md": "W25.md",
        "img_subdir": "W25",
        "redact_top": 75,
        "redact_bottom": 720,
    },
    {
        "pdf": "XM25.pdf",
        "md": "XM25.md",
        "img_subdir": "XM25",
        "redact_top": 65,
        "redact_bottom": 800,
    }
]

print("=== Starting PDF to Markdown Conversion (Method 1: Redaction of Header/Footer Images) ===")

orig_cwd = os.getcwd()
os.chdir(EXTRACTED_DIR)

try:
    for target in targets:
        pdf_name = target["pdf"]
        md_name = target["md"]
        img_sub = target["img_subdir"]
        redact_top = target["redact_top"]
        redact_bottom = target["redact_bottom"]
        
        pdf_path = os.path.join(BASE_DIR, pdf_name)
        md_path = os.path.join(EXTRACTED_DIR, md_name)
        img_rel_path = f"images/{img_sub}"
        
        # Clean existing image directory to purge old header images
        if os.path.exists(img_rel_path):
            shutil.rmtree(img_rel_path)
        os.makedirs(img_rel_path, exist_ok=True)
        
        if not os.path.exists(pdf_path):
            print(f"[ERROR] Not found: {pdf_path}")
            continue
            
        print(f"\n[Processing] {pdf_name} (Redact Top: {redact_top}pt, Redact Bottom: {redact_bottom}pt, Images: {img_rel_path})...")
        t0 = time.time()
        try:
            doc = pymupdf.open(pdf_path)
            
            # Apply redactions from page 2 onwards (index 1..len(doc)-1)
            # This completely removes header/footer images and text from PDF data structures
            for i in range(1, len(doc)):
                page = doc[i]
                pw = page.rect.width
                ph = page.rect.height
                
                # Header redaction
                page.add_redact_annot(pymupdf.Rect(0, 0, pw, redact_top))
                # Footer redaction
                page.add_redact_annot(pymupdf.Rect(0, redact_bottom, pw, ph))
                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE)
                
            # Convert to markdown with images extracted
            md_content = pymupdf4llm.to_markdown(
                doc,
                write_images=True,
                image_path=img_rel_path
            )
            
            # Remove messy picture text blocks (replaced by actual PNG images)
            md_content = re.sub(r'<!-- Start of picture text -->[\s\S]*?<!-- End of picture text -->', '', md_content)
            
            # Clean up leading empty lines and excessive consecutive blank lines
            md_content = md_content.lstrip()
            md_content = re.sub(r'\n{4,}', '\n\n\n', md_content)
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
                
            elapsed = time.time() - t0
            size_kb = os.path.getsize(md_path) / 1024
            line_count = md_content.count("\n") + 1
            img_count = len(os.listdir(img_rel_path))
            print(f"[Done] {md_name}: {line_count} lines, {size_kb:.1f} KB, {img_count} images extracted, elapsed: {elapsed:.2f}s")
        except Exception as e:
            print(f"[Error converting {pdf_name}]: {e}")
finally:
    os.chdir(orig_cwd)

print("\n=== All Conversions Completed ===")
