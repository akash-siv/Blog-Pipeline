#!/usr/bin/env python3
"""
blog_sync.py

This script syncs your blog posts from your Obsidian source to your Hugo blog.
It handles a folder structure like this:

  Source (e.g., /home/akash/test_source/Blog_Posts):
    Blog_Posts/
      ├── Book summary/
      │     ├── 4 hour work week.md
      │     ├── atomic habits.md
      │     ├── img25.jpg
      │     ├── img50.jpg
      │     └── img35.jpg
      ├── topic 2/
      │     ├── topic 1.md
      │     └── img80.jpg
      ├── another blog.md
      └── another img.jpg

  Destination (e.g., /home/akash/test_destination):
    test_destination/
      ├── content/
      │     └── (Markdown files are stored here preserving subfolders)
      └── static/
            └── images/
                   ├── img25.jpg
                   ├── img50.jpg
                   ├── img35.jpg
                   ├── img80.jpg
                   ├── another img.jpg
                   └── picture.webp

For each Markdown file:
  - It is copied from the source to the Hugo content folder while preserving subfolder structure.
  - Any Obsidian-style image link written as:
        [Hand Written Page 1](img25.jpg)
    is replaced with a proper Markdown image embed:
        ![Hand Written Page 1](/images/img25.jpg)
    and the referenced image (located in the same folder as the Markdown file) is copied to
    the Hugo static images folder.

Image files with extensions .jpg, .jpeg, .png, .gif, and .webp are synced into the Hugo static images folder (flattened).

The script only copies new or updated files and removes files from the destination that no longer exist in the source.
"""

import os
import re
import shutil

# === CONFIGURATION: Update these paths to match your system ===
# The root folder where your Obsidian posts (Markdown and images) reside.
SOURCE_POSTS_DIR = "/mnt/hugo_blog"

# Destination for Markdown files (Hugo content folder)
DEST_CONTENT_DIR = "/home/akash/hugo-blog/content/Blog_Posts"

# Destination for image files (Hugo static images folder)
DEST_IMAGES_DIR = "/home/akash/hugo-blog/static/images"

# Allowed image extensions (lowercase)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Regex pattern to match Obsidian-style image links of the form:
#   [Alt Text](image.jpg)
# This now supports .jpg, .jpeg, .png, .gif, and .webp formats.
IMAGE_LINK_PATTERN = re.compile(
    r'\[([^]]+)\]\(([^)]+\.(?:jpg|jpeg|png|gif|webp))\)',
    re.IGNORECASE
)
# ================================================================

def process_markdown_file(dest_filepath):
    """
    Processes a Markdown file in the destination content folder:
      - Finds Obsidian-style image links written as [Alt Text](image.ext)
      - Replaces them with Markdown image embeds: ![Alt Text](/images/image.ext)
      - Copies the referenced image (from the corresponding source folder)
        to the Hugo static images folder.
    """
    # Determine the relative directory of the Markdown file within DEST_CONTENT_DIR.
    rel_dir = os.path.relpath(os.path.dirname(dest_filepath), DEST_CONTENT_DIR)
    # The corresponding source folder is the same relative path under SOURCE_POSTS_DIR.
    source_dir = SOURCE_POSTS_DIR if rel_dir == '.' else os.path.join(SOURCE_POSTS_DIR, rel_dir)

    print(f"Processing Markdown: {dest_filepath}")
    try:
        with open(dest_filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading {dest_filepath}: {e}")
        return

    # Replacement function for re.sub()
    def repl(match):
        alt_text = match.group(1)
        image_ref = match.group(2)
        # Determine the source path for the image (assumed to be in the same folder as the Markdown file).
        image_source_path = os.path.join(source_dir, image_ref)
        if os.path.exists(image_source_path):
            dest_image_path = os.path.join(DEST_IMAGES_DIR, os.path.basename(image_ref))
            # Copy the image if it doesn't exist or is newer.
            if (not os.path.exists(dest_image_path)) or (os.path.getmtime(image_source_path) > os.path.getmtime(dest_image_path)):
                try:
                    shutil.copy2(image_source_path, dest_image_path)
                    print(f"  Copied image: {image_source_path} -> {dest_image_path}")
                except Exception as e:
                    print(f"  Error copying image {image_source_path}: {e}")
        else:
            print(f"  Warning: Image not found in source: {image_source_path}")

        # URL-encode spaces in the image filename.
        image_url = image_ref.replace(" ", "%20")
        # Return the corrected Markdown image embed.
        return f"[{alt_text}](/images/{os.path.basename(image_url)})"

    # Replace all occurrences of the image link pattern.
    new_content = re.sub(IMAGE_LINK_PATTERN, repl, content)
    if new_content != content:
        try:
            with open(dest_filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("  Updated image links in Markdown.")
        except Exception as e:
            print(f"  Error writing to {dest_filepath}: {e}")
    else:
        print("  No image links to update.")

def sync_markdown_files():
    """
    Walks through SOURCE_POSTS_DIR and syncs Markdown files (.md) to DEST_CONTENT_DIR.
    Processes each file if it is new or updated.
    """
    print("Syncing Markdown files...")
    for root, dirs, files in os.walk(SOURCE_POSTS_DIR):
        for file in files:
            if file.lower().endswith(".md"):
                source_file = os.path.join(root, file)
                # Compute the file's relative path with respect to SOURCE_POSTS_DIR.
                rel_path = os.path.relpath(source_file, SOURCE_POSTS_DIR)
                dest_file = os.path.join(DEST_CONTENT_DIR, rel_path)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                # Copy if the file is new or has been updated.
                if (not os.path.exists(dest_file)) or (os.path.getmtime(source_file) > os.path.getmtime(dest_file)):
                    try:
                        shutil.copy2(source_file, dest_file)
                        print(f"Copied Markdown: {source_file} -> {dest_file}")
                    except Exception as e:
                        print(f"Error copying {source_file} to {dest_file}: {e}")
                        continue
                    # Process the Markdown file to update image links.
                    process_markdown_file(dest_file)

def sync_image_files():
    """
    Walks through SOURCE_POSTS_DIR and syncs image files (jpg, jpeg, png, gif, webp) into DEST_IMAGES_DIR.
    The destination is a flat folder – images are copied using their basename.
    """
    print("Syncing image files...")
    for root, dirs, files in os.walk(SOURCE_POSTS_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                source_file = os.path.join(root, file)
                dest_file = os.path.join(DEST_IMAGES_DIR, file)
                os.makedirs(DEST_IMAGES_DIR, exist_ok=True)
                # Copy if the image is new or updated.
                if (not os.path.exists(dest_file)) or (os.path.getmtime(source_file) > os.path.getmtime(dest_file)):
                    try:
                        shutil.copy2(source_file, dest_file)
                        print(f"Copied Image: {source_file} -> {dest_file}")
                    except Exception as e:
                        print(f"Error copying image {source_file} to {dest_file}: {e}")

def remove_deleted_markdown():
    """
    Removes Markdown files from DEST_CONTENT_DIR that no longer exist in SOURCE_POSTS_DIR.
    """
    print("Removing deleted Markdown files...")
    for root, dirs, files in os.walk(DEST_CONTENT_DIR, topdown=False):
        for file in files:
            if file.lower().endswith(".md"):
                dest_file = os.path.join(root, file)
                rel_path = os.path.relpath(dest_file, DEST_CONTENT_DIR)
                source_file = os.path.join(SOURCE_POSTS_DIR, rel_path)
                if not os.path.exists(source_file):
                    try:
                        os.remove(dest_file)
                        print(f"Deleted Markdown: {dest_file}")
                    except Exception as e:
                        print(f"Error deleting {dest_file}: {e}")
        # Remove directories that no longer exist in the source.
        for dir_ in dirs:
            dest_dir = os.path.join(root, dir_)
            rel_dir = os.path.relpath(dest_dir, DEST_CONTENT_DIR)
            source_dir = os.path.join(SOURCE_POSTS_DIR, rel_dir)
            if not os.path.exists(source_dir):
                try:
                    shutil.rmtree(dest_dir)
                    print(f"Deleted directory: {dest_dir}")
                except Exception as e:
                    print(f"Error deleting directory {dest_dir}: {e}")

def remove_deleted_images():
    """
    Removes images from DEST_IMAGES_DIR that no longer exist anywhere in SOURCE_POSTS_DIR.
    (Comparison is based on the filename.)
    """
    print("Removing deleted image files...")
    # Build a set of all image basenames found in the source.
    source_images = set()
    for root, dirs, files in os.walk(SOURCE_POSTS_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                source_images.add(file)
    # In the destination images folder, delete any file not found in the source.
    if os.path.isdir(DEST_IMAGES_DIR):
        for file in os.listdir(DEST_IMAGES_DIR):
            if file not in source_images:
                dest_file = os.path.join(DEST_IMAGES_DIR, file)
                try:
                    os.remove(dest_file)
                    print(f"Deleted Image: {dest_file}")
                except Exception as e:
                    print(f"Error deleting image {dest_file}: {e}")

def main():
    # Check that the source directory exists.
    if not os.path.isdir(SOURCE_POSTS_DIR):
        print(f"Source directory does not exist: {SOURCE_POSTS_DIR}")
        return
    # Ensure that the destination directories exist.
    os.makedirs(DEST_CONTENT_DIR, exist_ok=True)
    os.makedirs(DEST_IMAGES_DIR, exist_ok=True)

    # Sync Markdown and image files.
    sync_markdown_files()
    sync_image_files()

    # Remove files from the destination that have been deleted in the source.
    remove_deleted_markdown()
    remove_deleted_images()

    print("Sync and processing complete.")

if __name__ == "__main__":
    main()
