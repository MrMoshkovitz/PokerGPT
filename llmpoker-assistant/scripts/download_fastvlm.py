"""
Download FastVLM Model

Downloads FastVLM-0.5B model from Hugging Face to local data directory.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_fastvlm(model_name: str = "fastvlm-0.5b", output_dir: str = "data/models"):
    """
    Download FastVLM model from Hugging Face.

    Args:
        model_name: Model variant to download
        output_dir: Directory to save model
    """
    try:
        from huggingface_hub import snapshot_download

        logger.info(f"Downloading {model_name} from Hugging Face...")
        logger.info("This may take several minutes (~500MB download)")

        # Map model names to HF repo IDs
        repo_map = {
            "fastvlm-0.5b": "apple/fastvlm-0.5b-stage3",
            "fastvlm-1.5b": "apple/fastvlm-1.5b-stage3",
            "fastvlm-7b": "apple/fastvlm-7b-stage3",
        }

        if model_name not in repo_map:
            logger.error(f"Unknown model: {model_name}")
            logger.info(f"Available models: {list(repo_map.keys())}")
            return False

        repo_id = repo_map[model_name]
        output_path = os.path.join(output_dir, model_name)

        # Create output directory
        os.makedirs(output_path, exist_ok=True)

        # Download model
        snapshot_download(
            repo_id=repo_id,
            local_dir=output_path,
            local_dir_use_symlinks=False,
        )

        logger.info(f"✓ Model downloaded successfully to {output_path}")
        return True

    except ImportError:
        logger.error(
            "huggingface_hub not installed. Run: pip install huggingface-hub"
        )
        return False
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return False


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "fastvlm-0.5b"
    success = download_fastvlm(model)
    sys.exit(0 if success else 1)
