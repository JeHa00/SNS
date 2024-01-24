import styled from "styled-components/macro";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Working_Img from "../logo_img/construction.png";

const FeedInfoBlock = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;

const WorkingImg = styled.img`
  width: 200px;
`;

function FeedInfo() {
  const navigate = useNavigate();
  const backHandler = () => {
    navigate("/main");
  };
  return (
    <FeedInfoBlock>
      <Header
        menuHandler={backHandler}
        feed={false}
        noti={false}
        mypage={false}
        scroll={true}
      />
      <WorkingImg src={Working_Img} />
      <div>서비스 준비 중 입니다.</div>
    </FeedInfoBlock>
  );
}

export default FeedInfo;
