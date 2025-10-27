import aws_cdk as core
import aws_cdk.assertions as assertions

from mobiltex_datalake_cdk.mobiltex_datalake_cdk_stack import MobiltexDatalakeCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in mobiltex_datalake_cdk/mobiltex_datalake_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MobiltexDatalakeCdkStack(app, "mobiltex-datalake-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
