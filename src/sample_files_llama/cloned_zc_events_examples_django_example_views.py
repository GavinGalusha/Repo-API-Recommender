from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response


class FakeObj(object):
    pk = -1


class AddSerializer(serializers.Serializer):
    x = serializers.IntegerField(required=True)
    y = serializers.IntegerField(required=True)


class AnswerSerializer(serializers.Serializer):
    answer = serializers.IntegerField(required=True)
    method = serializers.CharField(required=True)


class AddView(ViewSet):

    def _add(self, request, pk=None):
        question = AddSerializer(data=request.data)
        question.is_valid(raise_exception=True)
        valid_data = question.validated_data
        answer = valid_data['x'] + valid_data['y']
        answer_obj = FakeObj()
        answer_obj.answer = answer
        answer_obj.method = request.method
        answer_obj.pk = pk if pk else answer_obj.pk
        answer_serialized = AnswerSerializer(answer_obj)
        return Response(answer_serialized.data)

    def create(self, request):
        return self._add(request)

    def list(self, request):
        return self._add(request)

    def retrieve(self, request, pk=None):
        return self._add(request, pk=pk)

    def update(self, request, pk=None):
        return self._add(request, pk=pk)

    def destroy(self, request, pk=None):
        return self._add(request, pk=pk)


class LookupView(APIView):

    def get(self, request):
        x = request.query_params.get('x')
        return_value = 'y' if x else x
        return_status = status.HTTP_200_OK if x else status.HTTP_400_BAD_REQUEST
        return Response(return_value, status=return_status)
