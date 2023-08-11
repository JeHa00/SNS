import styled from "styled-components/macro";
import { Link } from "react-router-dom";

const SignupForm = styled.form`
  display: flex;
  flex-direction: column;
`;

function Login() {
  return (
    <div>
      <SignupForm>
        <div>
          <label for='email'>이메일</label>
          <input id='email'></input>
        </div>
        <div>
          <label for='pasword'>비밀번호</label>
          <input id='pasword'></input>
        </div>
        <div>
          <label for='pasword-check'>비밀번호 확인</label>
          <input id='pasword-check'></input>
        </div>
        <button>회원가입</button>
      </SignupForm>
    </div>
  );
}

export default Login;
