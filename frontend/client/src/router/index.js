import { createWebHistory, createRouter } from "vue-router";
import HomePage  from "@/views/HomePage.vue";
import LoginPage from "@/views/LoginPage.vue";
import RegisterPage from "@/views/RegisterPage.vue";
import UserPage from "@/views/UserPage.vue";
import HistoryPage from "@/views/HistoryPage.vue";
import FavoritePage from "@/views/FavoritePage.vue";
import MoviePage from "@/views/MoviePage.vue";
import StaffLogin from "@/views/StaffLogin.vue";
import SearchPage from "@/views/SearchPage.vue";


const routes = [
    {
        path: "/",
        name: "movieweb",
        component: HomePage,
    },

    {
        path: "/login",
        name: "loginpage",
        component: LoginPage,
    },

    {
        path: "/register",
        name: "registerpage",
        component: RegisterPage,
    },

    {
        path: '/user/:userId',
        name: 'userdetail',
        component: UserPage,
        props: true  
    },

    {
        path: "/history/:userId",
        name: "historyrpage",
        component: HistoryPage,
        props: true  
    },

    {
        path: "/favorite/:userId",
        name: "favoriterpage",
        component: FavoritePage,
        props: true  
    },

    {
        path: "/movie/:movieId",
        name: "moviepage",
        component: MoviePage,
        props: true  
    },

    {
        path: "/stafflogin",
        name: "staffloginpage",
        component: StaffLogin,
    },

    {
        path: "/search",
        name: "searchPage",
        component: SearchPage,
    },

]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

export default router;  