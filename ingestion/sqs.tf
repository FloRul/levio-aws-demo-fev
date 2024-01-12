resource "aws_sqs_queue" "dead_letter_queue" {
  name = "${var.queue_name}_dead_letter"
}

resource "aws_sqs_queue" "queue" {
  name = var.queue_name

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter_queue.arn
    maxReceiveCount     = 5
  })
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.ingestion_source_storage.id

  queue {
    queue_arn     = aws_sqs_queue.queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".pdf"
  }
}


resource "aws_lambda_event_source_mapping" "event_source_mapping" {
  event_source_arn = aws_sqs_queue.queue.arn
  enabled          = true
  function_name    = var.lambda_function_name
  batch_size       = 1
}

data "aws_iam_policy_document" "sqs_policy" {
  statement {
    actions = ["sqs:SendMessage"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    resources = [aws_sqs_queue.queue.arn]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.ingestion_source_storage.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "sqs_policy" {
  queue_url = aws_sqs_queue.queue.url
  policy    = data.aws_iam_policy_document.sqs_policy.json
}

output "queue_url" {
  description = "The URL of the SQS queue"
  value       = aws_sqs_queue.queue.url
}

output "dead_letter_queue_url" {
  description = "The URL of the Dead Letter Queue"
  value       = aws_sqs_queue.dead_letter_queue.url
}
