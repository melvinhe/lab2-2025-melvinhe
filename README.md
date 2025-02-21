# Due date: March 11, 2024 at 11:59 P.M.

# Lab 2: Matrix Multiplication - Tiling & Caches

At this point in the course, we have seen how neural networks are trained and evaluated from an algorithmic perspective. In this lab, we will see how these algorithms are optimized for performance on CPUs. Our goal is to get a more complete understanding of how software interacts with the CPU at an architectural level, and then optimize it so that it is cache-friendly.

In this lab, we will analyze how matrix multiplication can be optimized for caching. We simplified the behavior of caches in [./workspace/lab2/cache.py](./workspace/lab2/cache.py), and we will simulate cache hit/miss throughout matrix multiplication. Our final objective will be optimizing matrix multiplication for small cache energy and size. For detailed instructions, please read [./workspace/lab2/README.md](./workspace/lab2/README.md). 

## Using Docker

Please start the Docker (and the Jupyter server) same as in Lab 1 and 2, please pull the docker first and then start with `docker-compose up`. 
```
cd <your-git-repo-for-lab2>
docker-compose pull
docker-compose up
```
After finishing the lab, please commit all changes and push back to this repository.


## Submission
Submit a zip file on Canvas. The directory and contents of the files to be submitted are as follows:

```
your name/workspace/lab1/
  ├── answers.yaml
  ├── 1_pytorch_dnn.ipynb
  ├── 2_first_principles.ipynb
  ├── 3_hardware.ipynb
```