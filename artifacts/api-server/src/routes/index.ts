import { Router, type IRouter } from "express";
import healthRouter from "./health";
import trendsRouter from "./trends";
import watchlistRouter from "./watchlist";

const router: IRouter = Router();

router.use(healthRouter);
router.use(trendsRouter);
router.use(watchlistRouter);

export default router;
