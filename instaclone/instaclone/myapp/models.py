from __future__ import unicode_literals
from django.db import models
import uuid

class User(models.Model):
	email = models.EmailField()
	name = models.CharField(max_length=120)
	username = models.CharField(max_length=120)
	password = models.CharField(max_length=40)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)



class SessionToken(models.Model):
	user = models.ForeignKey(User)
	session_token = models.CharField(max_length=255)
	last_request_on = models.DateTimeField(auto_now=True)
	created_on = models.DateTimeField(auto_now_add=True)
	is_valid = models.BooleanField(default=True)

	def create_token(self):
		self.session_token = uuid.uuid4()

class PostModel(models.Model):
  user = models.ForeignKey(User)
  image = models.FileField(upload_to='user_images')
  image_url = models.CharField(max_length=255)
  caption = models.CharField(max_length=240)
  created_on = models.DateTimeField(auto_now_add=True)
  updated_on = models.DateTimeField(auto_now=True)
  has_liked = False

  def like_count(self):
	  return len(LikeModel.objects.filter(post=self))

  def comments(self):
		return CommentModel.objects.filter(post=self).order_by('-created_on')

class LikeModel(models.Model):
	user = models.ForeignKey(User)
	post = models.ForeignKey(PostModel)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)


class CommentModel(models.Model):
	user = models.ForeignKey(User)
	post = models.ForeignKey(PostModel)
	comment_text = models.CharField(max_length=555)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)


class BrandModel(models.Model):
	name = models.CharField(max_length=255)
	points = models.IntegerField(default=1)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)


class PointsModel(models.Model):
	user = models.ForeignKey(User)
	brand = models.ForeignKey(BrandModel)
	points = models.IntegerField(default=1)
	total_points = 0
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)
