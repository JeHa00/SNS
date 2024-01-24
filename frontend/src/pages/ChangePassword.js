import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import styled from "styled-components/macro";
import Header from "../components/Header";

const Input = styled.div`
  display: flex;
  justify-content: space-around;
`;

function ChangePassword() {
  const navigate = useNavigate();
  const backHandler = () => {
    navigate("/userfeed");
  };
  return (
    <div>
      <Header
        feed={false}
        menuHandler={backHandler}
        noti={false}
        mypage={false}
      />
      <Input>
        <div>기존 비밀번호</div>
        <div>입력창</div>
      </Input>
      <Input>
        <div>새로운 비밀번호</div>
        <div>입력창</div>
      </Input>
      <Input>
        <div>새로운 비밀번호 확인</div>
        <div>입력창</div>
      </Input>
    </div>
  );
}

export default ChangePassword;
