import os

def get_base_path():
    """
        Returns:
            Base path to the root directory - Wellness Vault
    """

    base_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".."
        )
    )

    return base_path