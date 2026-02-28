from django.test import TestCase

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from community.models import Post, Comment, Tag, Like


class CommunityViewAccessTestCase(TestCase):
    """Tests for community view access control"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='comuser1',
            email='comuser1@example.com',
            password='Pass123!',
            full_name='Community User',
            user_type='student',
            email_verified=True,
        )

    def test_community_requires_login(self):
        response = self.client.get(reverse('community:community'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_community_home_returns_200_when_authenticated(self):
        self.client.login(username='comuser1', password='Pass123!')
        response = self.client.get(reverse('community:community'))
        self.assertEqual(response.status_code, 200)

    def test_community_uses_correct_template(self):
        self.client.login(username='comuser1', password='Pass123!')
        response = self.client.get(reverse('community:community'))
        self.assertTemplateUsed(response, 'community/community.html')

    def test_community_home_section_loads(self):
        self.client.login(username='comuser1', password='Pass123!')
        response = self.client.get(reverse('community:community') + '?section=home')
        self.assertEqual(response.status_code, 200)

    def test_community_my_posts_section_loads(self):
        self.client.login(username='comuser1', password='Pass123!')
        response = self.client.get(reverse('community:community') + '?section=my-posts')
        self.assertEqual(response.status_code, 200)

    def test_community_create_post_section_loads(self):
        self.client.login(username='comuser1', password='Pass123!')
        response = self.client.get(reverse('community:community') + '?section=create-post')
        self.assertEqual(response.status_code, 200)


class PostCreationTestCase(TestCase):
    """Tests for creating posts"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='postauthor',
            email='postauthor@example.com',
            password='Pass123!',
            full_name='Post Author',
            user_type='student',
            email_verified=True,
        )
        self.client.login(username='postauthor', password='Pass123!')

    def test_create_post_successfully(self):
        response = self.client.post(
            reverse('community:community') + '?section=create-post',
            data={
                'title': 'My First Post',
                'content': 'This is the body of my first post.',
                'post_type': 'discussion',
            }
        )
        # Should redirect after successful creation
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Post.objects.filter(title='My First Post', author=self.user).exists())

    def test_create_post_without_title_fails(self):
        initial_count = Post.objects.count()
        self.client.post(
            reverse('community:community') + '?section=create-post',
            data={
                'title': '',
                'content': 'Content without a title.',
                'post_type': 'discussion',
            }
        )
        self.assertEqual(Post.objects.count(), initial_count)

    def test_create_post_requires_login(self):
        client = Client()
        response = client.post(
            reverse('community:community') + '?section=create-post',
            data={
                'title': 'Unauthenticated Post',
                'content': 'Should not be created.',
                'post_type': 'discussion',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(title='Unauthenticated Post').exists())


class PostDetailTestCase(TestCase):
    """Tests for viewing post details"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewpostuser',
            email='viewpostuser@example.com',
            password='Pass123!',
            full_name='View Post User',
            user_type='student',
            email_verified=True,
        )
        self.post = Post.objects.create(
            author=self.user,
            title='A Viewable Post',
            content='Post content here.',
            post_type='discussion',
        )
        self.client.login(username='viewpostuser', password='Pass123!')

    def test_post_detail_returns_200_or_redirects(self):
        """post_detail may redirect to community main page with section param"""
        response = self.client.get(
            reverse('community:post_detail', kwargs={'slug': self.post.slug})
        )
        # Some post detail views redirect to community/?section=post-detail
        self.assertIn(response.status_code, [200, 302])

    def test_post_detail_via_community_view(self):
        """Post detail via section parameter renders correctly"""
        response = self.client.get(
            reverse('community:community') + f'?section=post-detail&slug={self.post.slug}'
        )
        self.assertEqual(response.status_code, 200)


class ToggleLikeTestCase(TestCase):
    """Tests for the like/unlike functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='likeuser',
            email='likeuser@example.com',
            password='Pass123!',
            full_name='Like User',
            user_type='student',
            email_verified=True,
        )
        self.post = Post.objects.create(
            author=self.user,
            title='Likeable Post',
            content='Like me.',
            post_type='discussion',
        )
        self.client.login(username='likeuser', password='Pass123!')

    def test_toggle_like_returns_json(self):
        """toggle_like expects content_type and content_id params"""
        response = self.client.post(
            reverse('community:toggle_like'),
            data={'content_type': 'post', 'content_id': str(self.post.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_toggle_like_requires_login(self):
        client = Client()
        response = client.post(
            reverse('community:toggle_like'),
            data={'post_id': str(self.post.id)},
        )
        self.assertEqual(response.status_code, 302)


class PostModelTestCase(TestCase):
    """Tests for the Post model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser',
            email='modeluser@example.com',
            password='Pass123!',
        )

    def test_post_slug_auto_generated(self):
        post = Post.objects.create(
            author=self.user,
            title='Slug Auto Test',
            content='Content.',
            post_type='discussion',
        )
        self.assertIsNotNone(post.slug)
        self.assertTrue(len(post.slug) > 0)

    def test_post_str_returns_title(self):
        post = Post.objects.create(
            author=self.user,
            title='My Model Post',
            content='Content.',
            post_type='question',
        )
        self.assertEqual(str(post), 'My Model Post')

    def test_post_likes_count_property(self):
        post = Post.objects.create(
            author=self.user,
            title='Likes Count Post',
            content='Content.',
            post_type='discussion',
        )
        self.assertEqual(post.likes_count, 0)

    def test_duplicate_titles_get_unique_slugs(self):
        post1 = Post.objects.create(
            author=self.user,
            title='Duplicate Title',
            content='First.',
            post_type='discussion',
        )
        post2 = Post.objects.create(
            author=self.user,
            title='Duplicate Title',
            content='Second.',
            post_type='discussion',
        )
        self.assertNotEqual(post1.slug, post2.slug)

