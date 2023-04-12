from typing import Dict, List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.test.conftest import fake_user
from sns.users.test.utils import random_lower_string
from sns.posts.test.conftest import fake_post, fake_multi_posts
from sns.posts.schema import PostCreate, PostUpdate
from sns.posts.model import Post
from sns.posts.service import (
    get_post,
    get_multi_posts, 
    create, 
    update, 
    remove
)

def test_create(client: TestClient, db_session: Session, fake_user: Dict):
    writer = fake_user.get("user")
    post_info = PostCreate(content=random_lower_string(k=1000))
    post = create(db_session, post_info, writer.id)
    
    assert post
    assert hasattr(post, 'id')
    assert post.id == 1
    assert hasattr(post, 'content')
    assert hasattr(post, 'writer_id')
    assert post.writer_id == writer.id
    assert hasattr(post, 'writer')
    assert post.writer == writer
    assert hasattr(post, 'created_at')
    assert hasattr(post, 'updated_at')


def test_get_post(client: TestClient, db_session: Session, fake_post: Post, fake_user: Dict):
    writer = fake_user.get("user")
    post = get_post(db_session, fake_post.id)

    assert post
    assert hasattr(post, 'id')
    assert post.id == 1
    assert hasattr(post, 'content')
    assert hasattr(post, 'writer_id')
    assert post.writer_id == writer.id
    assert hasattr(post, 'writer')
    assert post.writer == writer
    assert hasattr(post, 'created_at')
    assert hasattr(post, 'updated_at')


def test_get_multi_posts(client: TestClient, db_session: Session, fake_multi_posts: List[Post], fake_user: Dict):
    writer = fake_user.get("user")
    posts = get_multi_posts(db_session, writer.id)
    
    assert posts
    assert len(posts) == 100
    for post in posts:
        assert hasattr(post, 'id')
        assert hasattr(post, 'content')
        assert hasattr(post, 'writer_id')
        assert post.writer_id == writer.id
        assert hasattr(post, 'writer')
        assert post.writer == writer
        assert hasattr(post, 'created_at')
        assert hasattr(post, 'updated_at')


def test_update_only_one_by_int(client: TestClient, db_session: Session, fake_post: Post):
    content_before_update = fake_post.content # 업데이트 전 내용
    data_to_be_updated = PostUpdate(content="Hello World!") # 업데이트할 내용
    post = update(db_session, post_info=fake_post.id, data_to_be_updated=data_to_be_updated) # 업데이트된 포스트
    content_after_update = post.content # 업데이트된 내용
    
    assert content_after_update == "Hello World!"
    assert content_before_update != content_after_update


def test_update_only_one_by_model_object(client: TestClient, db_session: Session, fake_post: Post):
    content_before_update = fake_post.content # 업데이트 전 내용
    data_to_be_updated = PostUpdate(content="Hello World!") # 업데이트할 내용
    post = update(db_session, post_info=fake_post, data_to_be_updated=data_to_be_updated) # 업데이트된 포스트
    content_after_update = post.content # 업데이트된 내용
    
    assert content_after_update == "Hello World!"
    assert content_before_update != content_after_update


def test_update_multi_posts_by_int(client: TestClient, db_session: Session, fake_user: Dict, fake_multi_posts: List[Post]):
    # 생성한 post 목록들
    user = fake_user.get("user")
    posts = get_multi_posts(db_session, user.id)
    
    data_to_be_updated = PostUpdate(content="Hello World!") # 업데이트할 내용
    for post in posts:
        update(db_session, post_info=post.id, data_to_be_updated=data_to_be_updated)
        assert post.content == "Hello World!"


# FIXME: int를 사용하여 post를 조회 후 업데이트하는 걸 여러 post에 시도 시 문제가 없지만, model object를 사용하면 문제가 발생된다.
# FIXME: post model 객체 정보는 넘어가지만, update 내부 jsonable_encoder 가 반환 시 첫 번째 model object만 값을 반환한다.
def test_update_multi_posts_by_model_object(client: TestClient, db_session: Session, fake_user: Dict, fake_multi_posts: List[Post]):
    print()
    # 생성한 post 목록들
    user = fake_user.get("user")
    posts = get_multi_posts(db_session, user.id)

    data_to_be_updated = PostUpdate(content="Hello World!") # 업데이트할 내용
    
    for post in posts:
        assert hasattr(post, "content") # NOTE: 이게 없으면 위에 FIXME 문제 발생
        update(db_session, post_info=post, data_to_be_updated=data_to_be_updated)
        assert post.content == "Hello World!"


def test_delete_only_one_by_int(client: TestClient, db_session: Session, fake_post: Post):
    post_id = fake_post.id
    remove(db_session, post_info=post_id)
    post = get_post(db_session, post_id=post_id)
    
    assert post == None


def test_delete_only_one_by_model_object(client: TestClient, db_session: Session, fake_post: Post):
    post_id = fake_post.id
    remove(db_session, post_info=fake_post)
    post = get_post(db_session, post_id=post_id)
    
    assert post == None    
    

def test_delete_multi_posts_by_int(client: TestClient, db_session: Session, fake_user: Dict, fake_multi_posts: List[Post]):
  # 생성한 post 목록들
    user = fake_user.get("user")
    posts = get_multi_posts(db_session, writer_id=user.id)

    for post in posts:
        remove(db_session, post_info=post.id)
    
    posts = get_multi_posts(db_session, writer_id=user.id)
    
    assert len(posts) == 0


def test_delete_multi_posts_by_model_object(client: TestClient, db_session: Session, fake_user: Dict, fake_multi_posts: List[Post]):
  # 생성한 post 목록들
    user = fake_user.get("user")
    posts = get_multi_posts(db_session, writer_id=user.id)

    for post in posts:
        remove(db_session, post_info=post)
    
    posts = get_multi_posts(db_session, writer_id=user.id)
    
    assert len(posts) == 0