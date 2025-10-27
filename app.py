#!/usr/bin/env python3
import aws_cdk as cdk
from mobiltex_datalake_cdk.datalake_stack import DataLakeStack

app = cdk.App()

DataLakeStack(
    app, "MobiltexDataLakeStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    ),
    description="Mobiltex Mini Data Lake - IoT sensor analytics infrastructure"
)

app.synth()
