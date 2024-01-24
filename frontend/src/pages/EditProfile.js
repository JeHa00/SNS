import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import styled from "styled-components/macro";
import Header from "../components/Header";

const Input = styled.div`
  display: flex;
  justify-content: space-around;
`;

function EditProfile() {
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
      <div>프로필 수정</div>
      <div>
        <Input>
          <div>프로필 사진</div>
          <div>입력창</div>
        </Input>
        <Input>
          <div>닉네임</div>
          <div>입력창</div>
        </Input>
        <Input>
          <div>프로필 메세지</div>
          <div>입력창</div>
        </Input>
      </div>
    </div>
  );
}

export default EditProfile;
