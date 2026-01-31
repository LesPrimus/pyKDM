from datetime import datetime, timedelta
from pathlib import Path

from pykdm import DCPCreator, KDMGenerator, KDMType


def main():
    # Example: Create a DCP
    try:
        dcp_creator = DCPCreator()
        print(f"DCP-o-matic version: {dcp_creator.version()}")

        # Create DCP from project
        # result = dcp_creator.create(
        #     project=Path("/path/to/project.dcp"),
        #     output=Path("/path/to/output"),
        #     encrypt=True,
        # )
        # print(f"DCP created at: {result.output_path}")

    except Exception as e:
        print(f"DCP Creator not available: {e}")

    # Example: Generate KDM
    try:
        kdm_generator = KDMGenerator()
        print(f"KDM CLI version: {kdm_generator.version()}")

        # Generate KDM for a DCP
        # valid_from = datetime.now()
        # valid_to = valid_from + timedelta(days=7)
        #
        # result = kdm_generator.generate(
        #     dcp=Path("/path/to/encrypted_dcp"),
        #     certificate=Path("/path/to/projector_cert.pem"),
        #     output=Path("/path/to/output.kdm.xml"),
        #     valid_from=valid_from,
        #     valid_to=valid_to,
        #     kdm_type=KDMType.MODIFIED_TRANSITIONAL_1,
        #     cinema_name="My Cinema",
        #     screen_name="Screen 1",
        # )
        # print(f"KDM created at: {result.output_path}")

    except Exception as e:
        print(f"KDM Generator not available: {e}")


if __name__ == "__main__":
    main()
