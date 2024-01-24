import { useRef } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components/macro";

const SettingContainer = styled.div`
  width: 100%;
  height: 100%;
  position: fixed;
  top: 0;
  left: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
`;
const Setting = styled.div`
  border: 1px solid black;
  width: 200px;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-around;
  background-color: #ffffff;
`;

function SettingBox({ modalCloseHandler, setCloseSetting }) {
  const modalRef = useRef();
  const outModalCloseHandler = (e) => {
    if (e.target === modalRef.current) setCloseSetting(false);
  };

  return (
    <SettingContainer ref={modalRef} onClick={outModalCloseHandler}>
      <Setting>
        <div onClick={modalCloseHandler}>닫기 x </div>
        <Link to='/edit-profile'>
          <div>프로필 수정</div>
        </Link>
        <Link to='/change-password'>
          <div>비밀번호 변경</div>
        </Link>
        <Link to='/'>
          <div>로그아웃</div>
        </Link>
        <div>회원 탈퇴</div>
      </Setting>
    </SettingContainer>
  );
}

export default SettingBox;
