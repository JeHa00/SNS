import styled from "styled-components/macro";
import { Link } from "react-router-dom";

const LoginForm = styled.form`
  width: 300px;
  height: 300px;
  display: flex;
  flex-direction: column;
  input:focus {
    outline: 1px solid green;
  }
`;

function Login() {
  return (
    <div>
      <LoginForm>
        <div>
          <label for='email'>이메일</label>
          <input id='email'></input>
        </div>
        <div>
          <label for='pasword'>비밀번호</label>
          <input id='pasword'></input>
        </div>
        <button>로그인</button>
      </LoginForm>
      <div>
        회원이 아니신가요? <Link to='/signup'>회원가입</Link>
      </div>
    </div>
  );
}

export default Login;
