import time
from datetime import datetime
import boto3
import urllib3
import myvalues

client_cloudwatch = boto3.client('cloudwatch')
client_events = boto3.client('events')
lambda_client = boto3.client('lambda')

url1 = 'https://fbref.com/en/'
url2 = 'https://github.com'
metricNamePerm = 'devops'
http = urllib3.PoolManager()


class MetricsResults:
    def __init__(self, url: str, latency: float, status: int):
        self.url = url
        self.latency = latency
        self.status = status

    def get_info(self):
        return f"{self.url} has latency of {self.latency} and status of {self.status}"


def index_handler(event, context):
    results1 = getMetrics(url1)
    putMetrics(metricNamePerm, url1, 'latency', results1.latency)
    putMetrics(metricNamePerm, url1, 'status', results1.status)

    results2 = getMetrics(url2)
    putMetrics(metricNamePerm, url2, 'latency', results2.latency)
    putMetrics(metricNamePerm, url2, 'status', results2.status)

    return f"{results1.get_info()} {results2.get_info()}"


def getMetrics(url: str) -> MetricsResults:
    start = time.time()
    http.request('GET', url)
    end = time.time()
    latency = end - start
    if latency > 1:
        status = 0
    else:
        status = 1
    results = MetricsResults(url, latency, status)
    return results


def putMetrics(metricName: str, dimensionName: str, dimensionValue: str, value):
    client_cloudwatch.put_metric_data(
        Namespace='devops',
        MetricData=[
            {
                'MetricName': metricName,
                'Dimensions': [
                    {
                        'Name': dimensionName,
                        'Value': dimensionValue
                    },
                ],
                'Timestamp': datetime.now(),
                'Value': value
            },
        ]
    )
