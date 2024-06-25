from rest_framework_xml.renderers import XMLRenderer

from rest_framework import serializers


class UploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    