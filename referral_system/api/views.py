import random
import string

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from referral_system.settings import EMAIL_HOST_USER
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, Referral
from .serializers import UserSerializers, ReferralSerializers


# import authtoken_token


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializers

    def login(self, request):
        phone_number = self.request.POST.get('phone_number')
        if self.queryset.filter(phone_number=phone_number).exists():
            user = get_object_or_404(self.queryset, phone_number=phone_number)
            letters_and_digits = string.ascii_letters + string.digits
            code = ''.join(random.choice(letters_and_digits) for i in range(4))
            send_mail('Verification code from Hammer Systems',
                      f'Enter this code: –> {code} <– for authorization on site.',
                      EMAIL_HOST_USER,
                      [user.email],
                      fail_silently=False, )
            data = {'secret_code': code}
            serializer = self.serializer_class(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(data='Secret code has been sent, please check your email!', status=status.HTTP_200_OK)
            return Response(f'{code} не сработал(')
        else:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, id: int, **kwargs):
        user = get_object_or_404(self.queryset, id=id)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def auth(self, request):
        secret_code = self.request.POST.get('secret_code')
        phone_number = self.request.POST.get('phone_number')
        email = self.request.POST.get('email')
        if secret_code is None:
            return Response(data="Secret code wasn't transmitted!", status=status.HTTP_400_BAD_REQUEST)
        if self.queryset.filter(secret_code=secret_code) is None:
            return Response(data="Secret code is incorrect!", status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(self.queryset, secret_code=secret_code, phone_number=phone_number, email=email)
        token = Token.objects.get(user=user).key
        return Response(token, status=status.HTTP_200_OK)


class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all()
    queryset_user = User.objects.all()
    serializer_class = ReferralSerializers
    serializer_class_user = UserSerializers
    permission_classes = [IsAuthenticated]

    def fill_invite_code(self, request, id: int):
        invite_code = self.request.data['invite_code']
        user = get_object_or_404(self.queryset_user, id=id)
        if self.request.user == user:
            if user.invite_code is None and user.ref_code != invite_code:
                referral_user = get_object_or_404(self.queryset_user, ref_code=invite_code)
                data = {'user': user.id, 'referral': referral_user.id}
                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                    data_user = {'invite_code': invite_code}
                    serializer_user = self.serializer_class_user(user, data=data_user, partial=True)
                    if serializer_user.is_valid():
                        serializer_user.save()
                        return Response(serializer_user.data, status=status.HTTP_200_OK)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(data='The invite code has already been entered or None!',
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(data='Access denied!', status=status.HTTP_403_FORBIDDEN)