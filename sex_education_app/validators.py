from django.contrib.auth.password_validation import MinimumLengthValidator


class ChineseMinimumLengthValidator(MinimumLengthValidator):
    """Django's minimum-length rule; its zh-hans translation is missing this message."""

    def get_error_message(self):
        return f"密码太短，至少需要 {self.min_length} 个字符。"

    def get_help_text(self):
        return f"密码至少需要 {self.min_length} 个字符。"
