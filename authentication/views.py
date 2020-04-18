import jwt
from django.conf import settings
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from rest_framework import authentication
from rest_framework import (
    generics,
    status,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.models import (
    User, UserProfile)
from authentication.permissions import (
    IsClientAdmin,
    IsProfileOwner,
    IsOwnerOrAdmin)
from authentication.renderer import UserJSONRenderer, ClientJSONRenderer
from django.core.exceptions import ObjectDoesNotExist
from authentication.serializers import (
    RegistrationSerializer,
    LoginSerializer, BlackListSerializer, ProfileSerializer)

# from utils import BaseUtils
from utils.permissions import IsViewerOrReadOnly, IsReviewer, IsAdmin


class RegistrationAPIView(generics.GenericAPIView):
    """Register new users."""
    serializer_class = RegistrationSerializer
    renderer_classes = (UserJSONRenderer,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        message = [
            request,
            user_data["email"]
        ]

        response = {
            "data": {
                "user": dict(user_data),
                "message": "Account created successfully",
                "status": "success"
            }
        }
        return Response(response, status=status.HTTP_201_CREATED)

class LoginAPIView(generics.GenericAPIView):
    """login a user via email"""
    serializer_class = LoginSerializer
    renderer_classes = (UserJSONRenderer,)

    def post(self, request):
        print('now here', request.data)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.data
        response = {
            "data": {
                "user": dict(user_data),
                "message": "You have successfully logged in",
                "status": "success"
            }
        }
        return Response(response, status=status.HTTP_200_OK)

class ProfileView(generics.GenericAPIView):
    """
    This View handles retreiving and updating of users profile
    """

    permission_classes = (IsAuthenticated, IsProfileOwner)
    serializer_class = ProfileSerializer

    def get(self, request):
        """
        Retreive a users profile without their security answer and question
        """
        user_object = User.objects.get(pk=request.user.pk)
        profile_data = {}
        try:
            profile = UserProfile.objects.get(user_id=request.user.pk)
            profile_data = model_to_dict(
                profile,
                fields=['recording_time','parental_lock','package'])
        except ObjectDoesNotExist:
            pass
        user_data = model_to_dict(
            user_object,
            fields=['id', 'email'])
        user_profile = { **user_data , **profile_data }
        # profile = UserProfile.objects.get(user=request.data)
        # print('user datasssss', profile)
        # profile_data = model_to_dict(
        #     user_data,
        #     exclude=['security_question', 'security_answer', 'is_deleted'])
        # profile_data['user'] = user_data
        # print('user datasssss', profile_data)
        data = {
            "data": {
                "profile": user_profile
            },
            "message": "Profile retreived successfully"
        }
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Update a users  profile
        """
        profile = UserProfile.objects.get(user=request.user)
        self.check_object_permissions(request, profile)
        profile_data = request.data

        serializer = self.serializer_class(
            profile, data=profile_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        updated_profile = dict(serializer.data)
        response = {
            "data": {
                "profile": updated_profile,
                "message": "Profile updated successfully"
            }
        }
        return Response(response, status=status.HTTP_200_OK)
