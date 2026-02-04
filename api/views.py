from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Cart, Order, OrderItem
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
import datetime


class UserRegistrationAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)
        data = serializer.data
        data["tokens"] = {"refresh": str(token),
                          "access": str(token.access_token)}
        return Response(data, status=status.HTTP_201_CREATED)


class UserLoginAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        serializer = CustomUserSerializer(user)
        token = RefreshToken.for_user(user)
        data = serializer.data
        data["tokens"] = {"refresh": str(token),
                          "access": str(token.access_token)}
        return Response(data, status=status.HTTP_200_OK)


class UserLogoutAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserInfoAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomUserSerializer

    def get_object(self):
        return self.request.user


@api_view(['GET'])
def getProducts(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getProduct(request, pk):
    product = Product.objects.get(id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


class GetCart(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        if 'qty' in request.data:
            product = Product.objects.get(id=pk)
            qty = request.data['qty']
            user = request.user
            try:
                cart = Cart.objects.get(user=user.id, product=product.id)
                cart.qty = qty
                cart.save()
                serializer = CartSerializer(cart, many=False)
                response = {'message': 'Cart updated',
                            'Result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                cart = Cart.objects.create(user=user, product=product, qty=qty)
                serializer = CartSerializer(cart, many=False)
                response = {'message': 'Product added to cart',
                            'Result': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'You need to provide quantity'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        cart = get_object_or_404(Cart, id=pk)
        if cart.user != request.user:
            return Response(
                {"detail": "You are not allowed to delete this product"},
                status=status.HTTP_403_FORBIDDEN
            )
        cart.delete()
        response = {'message': 'Product deleted from cart'}
        return Response(response, status=status.HTTP_204_NO_CONTENT)


class GetUsers(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request):
        User = get_user_model()
        users = User.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)


class CreateOrderFromCart(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        user = request.user

        with transaction.atomic():

            cart_items = Cart.objects.filter(user=user)

            if not cart_items.exists():
                return Response(
                    {"error": "Cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_price = sum(item.product.price *
                              item.qty for item in cart_items)
            order = Order.objects.create(
                user=user,
                total_price=total_price,
                date_of_payment=datetime.datetime.now(),
            )

            order_items_list = []
            for item in cart_items:
                order_item = OrderItem(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    qty=item.qty,
                    price=item.product.price,
                )
                order_items_list.append(order_item)

            OrderItem.objects.bulk_create(order_items_list)

            cart_items.delete()

            return Response(
                [{"message": "Order created successfully", "order_id": order.id}],
                status=status.HTTP_201_CREATED
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderItems(request, pk):
    order = OrderItem.objects.filter(order=pk)
    serializer = OrderItemSerializer(order, many=True)
    if not order.exists():
        return Response(
            {"error": "There is not order with this number"},
            status=status.HTTP_400_BAD_REQUEST
        )
    return Response(serializer.data)
