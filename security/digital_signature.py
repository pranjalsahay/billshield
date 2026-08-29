import os
import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


# Get the backend directory
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# Folder where RSA keys will be stored
KEYS_DIR = os.path.join(
    BASE_DIR,
    "keys"
)


# Private and public key paths
PRIVATE_KEY_PATH = os.path.join(
    KEYS_DIR,
    "private_key.pem"
)

PUBLIC_KEY_PATH = os.path.join(
    KEYS_DIR,
    "public_key.pem"
)


def generate_keys():
    """
    Generate RSA private and public keys.
    Keys are generated only if they do not already exist.
    """

    # Create keys folder if it does not exist
    os.makedirs(
        KEYS_DIR,
        exist_ok=True
    )

    # Do not generate new keys if keys already exist
    if (
        os.path.exists(PRIVATE_KEY_PATH)
        and os.path.exists(PUBLIC_KEY_PATH)
    ):
        return

    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Get corresponding public key
    public_key = private_key.public_key()

    # Save private key
    with open(
        PRIVATE_KEY_PATH,
        "wb"
    ) as private_file:

        private_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Save public key
    with open(
        PUBLIC_KEY_PATH,
        "wb"
    ) as public_file:

        public_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )


def sign_bill_hash(bill_hash: str) -> str:
    """
    Sign the SHA-256 bill hash using the RSA private key.

    Returns the signature as a Base64 encoded string.
    """

    # Make sure keys exist
    generate_keys()

    # Load private key
    with open(
        PRIVATE_KEY_PATH,
        "rb"
    ) as private_file:

        private_key = serialization.load_pem_private_key(
            private_file.read(),
            password=None
        )

    # Create digital signature
    signature = private_key.sign(
        bill_hash.encode(),
        padding.PSS(
            mgf=padding.MGF1(
                hashes.SHA256()
            ),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Convert binary signature to Base64 string
    return base64.b64encode(
        signature
    ).decode()


def verify_bill_signature(
    bill_hash: str,
    signature: str
) -> bool:
    """
    Verify the digital signature using the RSA public key.

    Returns True if the signature is valid.
    Returns False if the signature is invalid.
    """

    try:

        # Make sure keys exist
        generate_keys()

        # Load public key
        with open(
            PUBLIC_KEY_PATH,
            "rb"
        ) as public_file:

            public_key = serialization.load_pem_public_key(
                public_file.read()
            )

        # Convert Base64 signature back to bytes
        signature_bytes = base64.b64decode(
            signature
        )

        # Verify signature
        public_key.verify(
            signature_bytes,
            bill_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(
                    hashes.SHA256()
                ),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return True

    except Exception:
        return False