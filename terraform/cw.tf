### Lambda CW log group ###

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = 30

}


### App failure monitoring ###

resource "aws_cloudwatch_log_metric_filter" "lambda_crit_error_filter" {
  name           = "lambda_critical_error_filter"
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name
  pattern        = "{ $.message = %Critical error% }"
  metric_transformation {
    name      = "critical_error"
    namespace = "critical_errors"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "critical_error_alarm" {
  alarm_name          = "critical_error_alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  period              = 60
  metric_name         = aws_cloudwatch_log_metric_filter.lambda_crit_error_filter.name
  namespace           = aws_cloudwatch_log_metric_filter.lambda_crit_error_filter.metric_transformation[0].namespace
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.critical_error_notifications.arn]
}


### Guardian request monitoring ###

resource "aws_cloudwatch_log_metric_filter" "guardian_request_filter" {
  name           = "guardian_api_request_filter"
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name
  pattern        = "{ $.message = %request_content invoked% }"
  metric_transformation {
    name      = "api_request"
    namespace = "guardian_api_requests"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "guardian_request_limit_alarm" {
  alarm_name          = "guardian_rate_limit_alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  period              = 86400
  metric_name         = aws_cloudwatch_log_metric_filter.guardian_request_filter.name
  namespace           = aws_cloudwatch_log_metric_filter.guardian_request_filter.metric_transformation[0].namespace
  statistic           = "Sum"
  threshold           = 450
  alarm_actions       = [aws_sns_topic.guardian_request_limit_notifications.arn]
}