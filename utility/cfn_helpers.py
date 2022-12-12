import aws_cdk as cdk


def file_sub(file_name: str, variables: dict = None) -> str:

    with open(file_name, "r") as file:
        data = cdk.Fn.sub(file.read(), variables)

    return data
