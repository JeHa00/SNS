import { lazy, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import styled from "styled-components/macro";
import Header from "../components/Header";

const UserIfo = styled.div``;
const UserPosts = styled.div``;

const SettingBox = lazy(() => import("../components/Setting"));

function UserFeed() {
  const navigate = useNavigate();
  const [closeSetting, setCloseSetting] = useState(false);

  const modalCloseHandler = () => {
    setCloseSetting(!closeSetting);
  };
  const backHandler = () => {
    navigate("/main");
  };

  return (
    <div>
      <Header
        menuHandler={backHandler}
        feed={false}
        mypage={false}
        scroll={true}
      />
      <UserIfo>
        <div>
          <div>프로필사진</div>
          <div>유저닉네임</div> <div onClick={modalCloseHandler}>톱니바퀴</div>
        </div>
        <div>프로필메세지</div>
        <Link to='/follow-lists/followings'>
          <div>
            <span> 팔로잉20</span>
            <span> 팔로우 34</span>
          </div>
        </Link>
      </UserIfo>
      <UserPosts></UserPosts>
      {closeSetting && (
        <SettingBox
          modalCloseHandler={modalCloseHandler}
          setCloseSetting={setCloseSetting}
        />
      )}
    </div>
  );
}

export default UserFeed;
