from rest_framework import serializers
# nlp_generator/serializers.py
class ParagraphInputSerializer(serializers.Serializer):
     paragraph = serializers.CharField(trim_whitespace=False, allow_blank=True)
