import { Link } from "react-router-dom";
import styled from "styled-components/macro";
import Header from "../components/Header";

const Input = styled.div`
  display: flex;
  justify-content: space-around;
`;

function ResetPassword() {
  return (
    <div>
      <Header />
      <Input>
        <div>이메일</div>
        <div>입력창</div>
      </Input>
      <button>초기화</button>
      <div>
        초기화 버튼을 누르면 즉시 비밀번호가 초기화 되어 입력하신 이메일로
        비밀번호를 보내드립니다.
      </div>
    </div>
  );
}

export default ResetPassword;
