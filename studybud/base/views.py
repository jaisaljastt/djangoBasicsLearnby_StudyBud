from django.shortcuts import render, redirect
from django.http import HttpResponse
from . models import Room, Topic, Message
from . forms import RoomForm
from django.db.models import Q  # Import Q for complex queries
from django.contrib.auth.models import User  # Import User model for authentication
from django.contrib import messages  # Import messages for feedback
from django.contrib.auth import authenticate, login, logout  # Import authenticate and login for user authentication
from django.contrib.auth.decorators import login_required  # Import login_required to protect views

# Create your views here.

def loginPage(request):
    """
    Render the login page.
    """
    page = 'login'  # Set the page type to 'login'

    if request.user.is_authenticated:  # Check if the user is already authenticated
        return redirect('home')  # Redirect to the home page if already logged in

    if request.method == 'POST':
        username = request.POST.get('username').lower()  # Get the username from the POST request and convert it to lowercase
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)  # Fetch user by username
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)  # Authenticate user
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password is incorrect')
    context = {'page': page}  # Prepare context with the page type
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    """
    Log out the user and redirect to the home page.
    """
    logout(request)  # Log out the user
    return redirect('home')  # Redirect to the home page

def registerPage(request):
    """
    Render the registration page.
    """
    page = 'register'  # Set the page type to 'register'

    if request.user.is_authenticated:  # Check if the user is already authenticated
        return redirect('home')  # Redirect to the home page if already logged in

    if request.method == 'POST':
        username = request.POST.get('username').lower()  # Get the username from the POST request and convert it to lowercase
        password = request.POST.get('password')
        password2 = request.POST.get('re-enter_password')

        # Validate passwords
        if password != password2:
            messages.error(request, 'Passwords do not match')
        else:
            # Create a new user
            user = User.objects.create_user(username=username, password=password)
            user.save()  # Save the user to the database
            login(request, user)  # Log in the user
            return redirect('home')  # Redirect to the home page

    context = {'page': page}  # Prepare context with the page type
    return render(request, 'base/login_register.html', context)

def home(request):
    """
    Render the home page.
    """
    q = request.GET.get('q') if request.GET.get('q') != None else ''  # Get the query parameter 'q' from the request
    rooms = Room.objects.filter(Q(topic__name__icontains=q)|Q(name__icontains=q)|Q(description__icontains=q))  # Fetch all rooms from the database
    specific_room_count = rooms.count()  # Count the number of rooms that match the query
    topics = Topic.objects.all()  # Fetch all topics from the database (if needed)
    topics_count = topics.count()  # Count the number of topics
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))  # Fetch messages related to the rooms that match the query


    context = {'rooms': rooms, 'topics': topics, 'topics_count':topics_count, 
               'specific_room_count':specific_room_count, 'room_messages':room_messages}  # Prepare context with rooms
    return render(request, 'base/home.html', context)

def room(request, pk):
    """
    Render the room page.
    """     
    room = Room.objects.get(id=pk)  # Fetch the room by primary key
    participants = room.participants.all()  # Get all participants in the room
    room_messages = room.message_set.all()  # Fetch all messages related to the room
    if request.method == 'POST':
        new_message = request.POST.get('body')  # Get the new message from the POST request
        if request.user.is_authenticated and new_message:
            Message.objects.create(
                user=request.user,
                room=room,
                body=new_message
            )
            room.participants.add(request.user)  # Add the user to the participants of the room
            return redirect('room', pk=room.id)  # Redirect to clear the form and prevent resubmission
    context = {'room': room, 'room_messages':room_messages, 'participants':participants}  # Prepare context with the room
    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    """
    Render the user profile page.
    """
    user = User.objects.get(id=pk)  # Fetch the user by primary key
    rooms = user.room_set.all()  # Get all rooms created by the user
    room_messages = user.message_set.all()  # Get all messages sent by the user
    topics = Topic.objects.all()  # Fetch all topics from the database (if needed)
    topics_count = topics.count()  # Count the number of topics
    
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics, 'topics_count':topics_count}  # Prepare context with user data
    return render(request, 'base/profile.html', context)

  # Ensure that the user is logged in to access the room page
@login_required(login_url='login')  # Protect the view with login_required decorator
def createRoom(request):
    """
    Render the create room page.
    """
    form = RoomForm()  # Initialize the RoomForm
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)  # Save the form but do not commit to the database yet
            room.host = request.user  # Set the host of the room to the current user
            room.save()  # Save the room to the database
            return redirect('home')  # Redirect to the home page after saving
    context = {"form": form}  # Prepare context with the form
    return render(request, 'base/room_form.html', context)

  # Ensure that the user is logged in to access the room page
@login_required(login_url='login')  # Protect the view with login_required decorator
def updateRoom(request, pk):
    """
    Render the update room page.
    """
    room = Room.objects.get(id=pk)  # Fetch the room by primary key
    form = RoomForm(instance=room) 
    
    if request.user != room.host:
        return HttpResponse("You are not allowed here!")

     # Initialize the RoomForm with the room instance
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()  # Save the form if valid
            return redirect('home')  # Redirect to the home page after saving
    context = {"form": form}  # Prepare context with the form
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')  # Protect the view with login_required decorator
def deleteRoom(request, pk):
    """
    Render the delete room page.
    """
    room = Room.objects.get(id=pk)  # Fetch the room by primary key
    if request.user != room.host:
        return HttpResponse("You are not allowed here!")

    if request.method == 'POST':
        room.delete()  # Delete the room if POST request
        return redirect('home')  # Redirect to the home page after deletion
    context = {"object": room}  # Prepare context with the room object
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')  # Protect the view with login_required decorator
def deleteMessage(request, pk):
    """
    Render the delete message page.
    """
    message = Message.objects.get(id=pk)  # Fetch the message by primary key
    if request.user != message.user:
        return HttpResponse("You are not allowed here!")
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    context = {"object": message}
    return render(request, 'base/delete.html', context)