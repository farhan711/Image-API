# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
import json
import os

from django.core.files import File
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from file_system_jwt.authentication import JSONWebTokenAuthentication

from ImageAPI import settings


def valid_image_extension(file_name, extension_list=settings.VALID_IMAGE_EXTENSIONS):
    return any([file_name.endswith(e) for e in extension_list])


@api_view(['GET', 'POST'])
@authentication_classes((JSONWebTokenAuthentication,))
def user_image_list(request):
    """
        Method to handle the get and post requests on Image API,
        :GET 
            :returns 
                :username the username of the user
                :images the list of image names associated with the user
        
        :POST
            :param 
                form fields
                    :image image to be uploaded from form
                query params
                    :overwrite 
                        :true overwrites existing image with same name if any
                        :false(default) throws a 400 if image exists with given name
            :returns
                corresponding status codes and messages
                201 - success
                401 - user not authenticated
                400 - Image not given or if invalid image given or if Image already exists
    """
    if request.method == 'GET':
        """returns list of images uploaded by user"""
        images = os.listdir(request.user.image_folder)  # fetch images list
        return Response(dict(username=request.user.username, images=images))
    else:  # POST
        """Save file uploaded to user's images"""
        try:
            image = request.FILES['image']  # image file
        except MultiValueDictKeyError:  # no image sent
            return Response("Image not given, set the field name to image", status=status.HTTP_400_BAD_REQUEST)
        if not valid_image_extension(image.name):
            return Response("Give a valid image file { jpg, jpeg, gif, png}", status=status.HTTP_400_BAD_REQUEST)
        overwrite = json.loads(str.lower(request.query_params.get('overwrite', 'false')))
        image_path = os.path.join(request.user.image_folder, image.name)
        if os.path.isfile(image_path) and not overwrite:
            """image already exists and overwrite parameter is not true"""
            return Response("Image already exists, to overwrite send a overwrite=true as parameter",
                            status=status.HTTP_400_BAD_REQUEST)
        with open(image_path, 'wb') as destination:
            """save image to file/username path"""
            for chunk in image.chunks():
                destination.write(chunk)
            return Response("Image successfully uploaded", status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((JSONWebTokenAuthentication,))
def user_image(request, file_name):
    file_path = os.path.join(request.user.image_folder, file_name)
    if not os.path.isfile(file_path):
        return Response("Image not found", status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        try:
            image = open(file_path, 'rb')
            response = HttpResponse(File(image), content_type='image/*')
            response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
            return response
        except:
            return Response("Failed to fetch image", status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PATCH':
        image = request.FILES['image']
        with open(file_path, 'wb') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
            return Response("Image successfully modified", status=status.HTTP_201_CREATED)
    else:
        os.remove(file_path)
        return Response("Image successfully deleted", status=status.HTTP_200_OK)
