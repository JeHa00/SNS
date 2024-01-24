import { Suspense, lazy } from "react";
import { Link, Route, Routes } from "react-router-dom";
import styled from "styled-components/macro";
import Header from "../components/Header";

const Followers = lazy(() => import("../components/Followers"));
const Followings = lazy(() => import("../components/Followings"));

function FollowLists() {
  return (
    <div id='follow'>
      <Header />
      <div>
        <Link to='followings'>
          <div>
            팔로잉 <span>20</span>
          </div>
        </Link>
        <Link to='followers'>
          <div>
            팔로워 <span>13</span>
          </div>
        </Link>
      </div>
      <div>
        <Suspense fallback='팔로잉 목록 로딩ing'>
          <Routes>
            <Route path='followings' element={<Followings />} />
            <Route path='followers' element={<Followers />} />
          </Routes>
        </Suspense>
      </div>
    </div>
  );
}

export default FollowLists;
